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
#
# TODO: infer_implicit_action(previous_track, current_track, time_played_ms,
#                              track_duration_ms) -> str
#   playback_loop.py only observes "the song changed" -- this turns that
#   observation into an action label (quick skip vs full play vs replay)
#   based on how much of the previous track was played, mirroring
#   legacy_app/Atmofy.py's check_song_change/store_current_song logic but
#   producing a labeled action instead of a raw timestamp file.
