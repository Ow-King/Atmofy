# The outer/inner polling loop, moved here from app/spotify/auth.py's old
# main() so auth.py can stay auth-only. Orchestrates:
#   app/spotify/client.py (reads) + app/services/recommendation_service.py
#   (GNN + ranker) + app/spotify/queue.py (writes) + app/services/
#   feedback_service.py (logging) + app/services/context_buffer.py
#   (batches feedback writes -- see that file for the full design).
#
# TODO: get_spotify_client() from app/spotify/auth.py once that function
#   exists (see the TODO left in auth.py).
#
# TODO: def run():
#   - Authenticate once via app/spotify/auth.py.
#
#   - Outer loop:
#       - client.get_current_playlist_id(sp) to detect what playlist/
#         tracklist the user is currently on.
#       - client.get_playlist_tracks(sp, playlist_id) to pull that
#         playlist's track metadata (candidate pool for the recommender).
#
#       - Inner loop, while the user stays on this same playlist:
#           - Poll client.get_current_playback(sp) to detect a song change.
#           - Call context_buffer.maybe_flush(now) every iteration -- this
#             is what detects a quarter-hour slot rollover and batches the
#             previous window's buffered interactions into the DB (see
#             context_buffer.py for why it triggers on slot change rather
#             than a fixed timer).
#           - On a song change only (rate-limit weather calls): if more than
#             an hour has passed since the last weather fetch, call
#             app/features/weather.get_weather() again and rebuild the
#             context vector via app/features/full_parameters.py.
#           - Call recommendation_service.get_next_recommendations(...) to
#             top up the queue until there's a 3-song buffer, then
#             queue.queue_tracks(sp, ...) for any shortfall.
#           - Call feedback_service.record_interaction(...) for the song
#             that just finished/changed, using
#             feedback_service.infer_implicit_action(...) to label it. Note
#             this no longer writes to the DB directly -- it appends to
#             context_buffer's pending list (see context_buffer.py).
#
#       - When client.get_current_playlist_id(sp) no longer matches the
#         playlist tracked at the top of the outer loop: call
#         queue.clear_queue(sp) and queue.skip_to_next(sp), then restart the
#         outer loop for the new playlist.
#
# TODO: wrap the whole run() body in try/finally (or register via
#   atexit: https://docs.python.org/3/library/atexit.html) calling
#   context_buffer.flush_now() so a graceful shutdown doesn't discard the
#   current partial window. A non-graceful exit (crash/kill) may still lose
#   up to ~15 minutes of buffered feedback -- accepted tradeoff for this
#   project's scope, not something to engineer around further.
#
# TODO: decide polling interval / backoff (legacy_app/main.py used a flat
#   time.sleep(3) -- revisit whether that's still appropriate here or if it
#   should back off when nothing has changed, to reduce API calls).
#
# TODO: decide how this loop is started -- long-running process via the
#   `musicbot` CLI entry point per the .md spec, vs. an APScheduler job.

if __name__ == "__main__":
    pass
