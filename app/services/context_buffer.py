# Session-local write buffer sitting between feedback_service.py and
# app/database.py. Owns two decisions made while designing the `contexts`/
# `interactions` relationship (see conversation history / design notes):
#
#   1. `contexts` is a dimension table keyed on (date, quarter_hour_slot) --
#      one row per 15-minute window (matching time_features.get_quarter_hour_slot()
#      and weather.py's minutely_15 resolution), not one row per interaction.
#      Many interactions -> one context row (classic fact/dimension pattern).
#      `contexts` should have a UniqueConstraint on (date, quarter_hour_slot)
#      in app/database.py so a duplicate insert for the same slot is a DB
#      error, not a silent bug.
#      https://docs.sqlalchemy.org/en/20/core/constraints.html#unique-constraint
#
#   2. Interactions are NOT written to the DB one at a time. They're
#      buffered in memory and flushed in a batch exactly when the current
#      quarter-hour slot changes (not on a fixed wall-clock timer -- see
#      note on maybe_flush below for why that distinction matters), or when
#      the app exits gracefully. A non-graceful exit (crash/kill) may lose
#      the current buffer (up to ~15 minutes of feedback) -- accepted
#      tradeoff for this project's scope.
#

import pandas as pd

from feedback_service import Interaction
from datetime import date, datetime
from sqlalchemy import select

from app.database import Context, Interaction as InteractionRow, SessionLocal
from app.features.time_features import get_quarter_hour_slot
from app.features.full_parameters import get_next_3_hrs_parameters, update_next_3_hrs_parameters

pending_interactions: list[Interaction] = []
current_slot: tuple[date, int] | None = None
current_full_parameter_table: pd.DataFrame | None = None

# TODO: add_interaction(interaction: Interaction) -> None
#   Called by feedback_service.record_interaction instead of it writing to
#   app/database.py directly. Appends `interaction` (with context_id still
#   None/unresolved) to pending_interactions. Does NOT resolve context_id
#   here -- that only happens for the whole batch at flush time.

# Called by feedback_service.record_interaction, adds an interation without context to the pending table
def add_interaction(interatcion: Interaction) -> None:
    pending_interactions.append(interatcion)

# TODO: maybe_flush(now: datetime) -> None
#   Called every iteration of playback_loop.py's poll loop (the loop is
#   already waking up periodically, so no separate scheduler/thread needed).
#   slot = time_features.get_quarter_hour_slot(now), paired with now.date().
#   If current_slot is None: just set current_slot = (now.date(), slot) and
#   return (nothing buffered yet, nothing to flush).
#   If slot has NOT changed from current_slot: return (still mid-window).
#   If slot HAS changed: this is the flush trigger --
#     - resolve/create the ONE contexts row for the *old* current_slot
#       (look up by (date, quarter_hour_slot); insert via app/database.py
#       if it doesn't exist yet, using the context features computed for
#       that window via app/features/weather.py + full_parameters.py)
#     - stamp that context_id onto every Interaction in pending_interactions
#     - bulk-insert pending_interactions via app/database.py in one
#       transaction (SQLAlchemy: Session.add_all(), one commit)
#       https://docs.sqlalchemy.org/en/20/orm/session_basics.html#adding-new-or-existing-items
#     - clear pending_interactions, set current_slot = (now.date(), slot)
#   Triggering on slot CHANGE (not a generic 15-min timer) guarantees every
#   flushed batch belongs to exactly one contexts row -- a timer not phase
#   -aligned to :00/:15/:30/:45 could straddle a slot boundary and split a
#   batch across two different contexts.
def maybe_flush(now: datetime) -> None:
    global pending_interactions, current_slot, current_full_parameter_table

    active_quarter = get_quarter_hour_slot(now)

    # Set the current slot if it is not set yet
    if not current_slot:
        current_slot = (now.date(), active_quarter)

    # Check for any difference in the slots
    if current_slot != (now.date(), active_quarter):
        # Create the Context Row
        if not current_full_parameter_table:
            update_next_3_hrs_parameters(38.951, -92.334)
            current_full_parameter_table = get_next_3_hrs_parameters()

        row = current_full_parameter_table.set_index("quarter_hour_slot").loc[current_slot[1]]

        # Add the context ID to every interation in pending_interations
        with SessionLocal() as session:
            existing = session.scalars(
                select(Context).where(
                    Context.date == current_slot[0],
                    Context.quarter_hour_slot == current_slot[1],
                )
            ).first()

            if existing is not None:
                context_id = existing.id
            else:
                new_context = Context(
                    date = current_slot[0],
                    quarter_hour_slot = current_slot[1],
                    temperature_2m = float(row["temperature_2m"]),
                    cloud_cover = float(row["cloud_cover"]),
                    precipitation = float(row["precipitation"]),
                    weather_code = float(row["weather_code"]),
                    is_day = bool(row["is_day"]),
                    time_sin = float(row["time_sin"]),
                    time_cos = float(row["time_cos"]),
                    day_of_week = int(row["day_of_week"]),
                )
                session.add(new_context)
                session.flush()
                context_id = new_context.id

            # Build the real DB rows from the buffered dataclass instances,
            # stamping in the resolved context_id on each one
            data_to_insert = [
                InteractionRow(
                    track_id=interaction.track_id,
                    action=interaction.action,
                    weight=interaction.weight,
                    timestamp=interaction.timestamp,
                    source=interaction.source,
                    context_id=context_id,
                    model_version=interaction.model_version,
                    score=interaction.score,
                )
                for interaction in pending_interactions
            ]

            # Bulk insert -- same session/transaction as the context row
            # above, so the context (if newly created) and every interaction
            # commit together or not at all
            session.add_all(data_to_insert)
            session.commit()

            pending_interactions = []
            current_slot = (now.date(), active_quarter)



# TODO: flush_now() -> None
#   Force-flush whatever's pending regardless of slot, for the graceful-exit
#   path (see below) -- reuses the same "resolve context, bulk-insert,
#   clear buffer" logic as maybe_flush's flush branch, just without waiting
#   for a slot change first.

def flush_now() -> None:
    global pending_interactions, current_slot, current_full_parameter_table

    # Nothing has ever been buffered, so there's no slot to flush against.
    if not current_slot:
        return

    # Create the Context Row
    if not current_full_parameter_table:
        update_next_3_hrs_parameters(38.951, -92.334)
        current_full_parameter_table = get_next_3_hrs_parameters()

    row = current_full_parameter_table.set_index("quarter_hour_slot").loc[current_slot[1]]

    # Add the context ID to every interation in pending_interations
    with SessionLocal() as session:
        existing = session.scalars(
            select(Context).where(
                Context.date == current_slot[0],
                Context.quarter_hour_slot == current_slot[1],
            )
        ).first()

        if existing is not None:
            context_id = existing.id
        else:
            new_context = Context(
                date = current_slot[0],
                quarter_hour_slot = current_slot[1],
                temperature_2m = float(row["temperature_2m"]),
                cloud_cover = float(row["cloud_cover"]),
                precipitation = float(row["precipitation"]),
                weather_code = float(row["weather_code"]),
                is_day = bool(row["is_day"]),
                time_sin = float(row["time_sin"]),
                time_cos = float(row["time_cos"]),
                day_of_week = int(row["day_of_week"]),
            )
            session.add(new_context)
            session.flush()
            context_id = new_context.id

        # Build the real DB rows from the buffered dataclass instances,
        # stamping in the resolved context_id on each one
        data_to_insert = [
            InteractionRow(
                track_id=interaction.track_id,
                action=interaction.action,
                weight=interaction.weight,
                timestamp=interaction.timestamp,
                source=interaction.source,
                context_id=context_id,
                model_version=interaction.model_version,
                score=interaction.score,
            )
            for interaction in pending_interactions
        ]

        # Bulk insert -- same session/transaction as the context row above,
        # so the context (if newly created) and every interaction commit
        # together or not at all
        session.add_all(data_to_insert)
        session.commit()

        pending_interactions = []


# TODO: wire into playback_loop.py
#   - call maybe_flush(now) once per poll iteration inside the loop
#   - wrap the loop's run() body in try/finally (or register flush_now via
#     atexit: https://docs.python.org/3/library/atexit.html) so a graceful
#     shutdown (Ctrl+C, normal exit) flushes the final partial window
#     instead of discarding it