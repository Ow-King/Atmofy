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
# TODO: module state
#   pending_interactions: list[Interaction] = []
#   current_slot: tuple[date, int] | None = None   # (date, quarter_hour_slot)
#
# TODO: add_interaction(interaction: Interaction) -> None
#   Called by feedback_service.record_interaction instead of it writing to
#   app/database.py directly. Appends `interaction` (with context_id still
#   None/unresolved) to pending_interactions. Does NOT resolve context_id
#   here -- that only happens for the whole batch at flush time.
#
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
#
# TODO: flush_now() -> None
#   Force-flush whatever's pending regardless of slot, for the graceful-exit
#   path (see below) -- reuses the same "resolve context, bulk-insert,
#   clear buffer" logic as maybe_flush's flush branch, just without waiting
#   for a slot change first.
#
# TODO: wire into playback_loop.py
#   - call maybe_flush(now) once per poll iteration inside the loop
#   - wrap the loop's run() body in try/finally (or register flush_now via
#     atexit: https://docs.python.org/3/library/atexit.html) so a graceful
#     shutdown (Ctrl+C, normal exit) flushes the final partial window
#     instead of discarding it
