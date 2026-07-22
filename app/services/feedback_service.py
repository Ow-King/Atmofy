from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

class InteractionScore(IntEnum):
    SAVE = 3            # If the song is saved or liked on the UI
    REPLAY = 2          # If the song is restarted/still plaking past the expected time
    FULL_PLAY = 1       # If the song is different from the previous but still in the expected time
    LATE_SKIP = -1      # If the song is skipped late in the duration (after 50% of the duration)
    QUICK_SKIP = -2     # If the song is skipped early in the duration (before 50% of the duration)
    DISLIKE = -3        # If the song is disliked in the app UI


# Placeholder row shape matching the .md spec's `interactions` table columns.
# Swap this for whatever app/database.py ends up exposing (SQLAlchemy model
# or plain dict) once that file has a schema -- it's empty right now.
@dataclass
class Interaction:
    track_id: str
    action: str
    weight: int
    timestamp: datetime
    source: str
    context_id: int | None
    model_version: str | None
    score: float | None


# Records explicit/implicit feedback signals per the .md spec's `interactions`
# table (track_id, action, weight, timestamp, source, context_id,
# model_version, score). playback_loop.py should call into this whenever it
# observes a song change, skip, or (later) an explicit CLI feedback command.
#
# TODO: record_interaction(track_id, action, context, model_version=None,
#                           score=None, source="loop") -> None
#   Looks up the action's weight from the .md spec's table (manual queue/
#   save/like +3, replay +2, full play +1, ignore 0, quick skip -2,
#   dislike -3) and writes a row via app/database.py.
def record_interaction(track_id, action, context, model_version=None, score=None, source="loop") -> Interaction:
    # TODO 1: look up the weight for this action, e.g.
    #   weight = InteractionScore[action.upper()]
    #   (decide whether `action` is a plain string like "like"/"skip" or
    #   already an InteractionScore -- pick one and keep it consistent with
    #   whatever calls this, e.g. infer_implicit_action below.)
    weight = InteractionScore[action.upper()]

    # TODO 2: resolve context -> context_id.
    #   Design decision (see app/services/context_buffer.py): `contexts` is a
    #   dimension table keyed on (date, quarter_hour_slot) -- one row per
    #   15-minute window, not one per interaction. This function does NOT
    #   resolve context_id itself. Instead:
    #     - build the Interaction below with context_id=None (unresolved)
    #     - hand it to context_buffer.add_interaction(interaction) instead
    #       of writing to app/database.py directly
    #     - context_buffer owns resolving/creating the one contexts row per
    #       15-min slot and stamping context_id onto every buffered
    #       Interaction when it flushes (on slot change, or on app exit)
    #   `context` (the current arg) should end up being whatever
    #   context_buffer needs to tag the interaction with its slot -- likely
    #   just `datetime.now()`, since context_buffer derives the slot itself
    #   via time_features.get_quarter_hour_slot().

    # TODO 3: build the row: track_id, action, weight, datetime.now(),
    #   source, context_id=None (resolved later by context_buffer),
    #   model_version, score -- matching the .md spec's `interactions`
    #   table columns.

    # TODO 4: hand off to context_buffer.add_interaction(interaction) --
    #   NOT a direct app/database.py write. The buffer accumulates
    #   interactions in memory and only writes to the DB in batches, once
    #   per 15-minute slot (see context_buffer.py for why).
    pass


# TODO: infer_implicit_action(previous_track, current_track, time_played_ms,
#                              track_duration_ms) -> str
#   playback_loop.py only observes "the song changed" -- this turns that
#   observation into an action label (quick skip vs full play vs replay)
#   based on how much of the previous track was played, mirroring
#   legacy_app/Atmofy.py's check_song_change/store_current_song logic but
#   producing a labeled action instead of a raw timestamp file.
def infer_implicit_action(previous_track, current_track, time_played_ms, track_duration_ms) -> str:
    if previous_track == current_track:
        return "REPLAY"
    if time_played_ms == track_duration_ms:
        return "FULL_PLAY"
    elif time_played_ms < (track_duration_ms / 2):
        return "QUICK_SKIP"
    else:
        return "LATE_SKIP"
