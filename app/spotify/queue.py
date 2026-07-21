# Thin write-only wrapper around the spotipy client (from app/spotify/auth.py).
# Counterpart to client.py -- everything here mutates Spotify playback state,
# so keep these calls isolated and easy to mock/no-op in tests (you do not
# want tests accidentally skipping the user's real music).
#
# TODO: queue_track(sp, track_uri) -> None
#   Wraps sp.add_to_queue(track_uri). This is the "add one recommended song"
#   primitive that recommendation_service.py's output feeds into.
#
# TODO: queue_tracks(sp, track_uris) -> None
#   Convenience loop over queue_track for topping up the 3-song buffer in
#   one call from playback_loop.py.
#
# TODO: skip_to_next(sp) -> None
#   Wraps sp.next_track(). Used when playback_loop.py detects the playlist
#   changed and needs to move off whatever Spotify auto-queued.
#
# TODO: clear_queue(sp) -> None
#   Spotify's API has no direct "clear queue" endpoint -- confirm the
#   approach here (e.g. skip_to_next() repeatedly until the queue is drained,
#   or toggle repeat/context off) before implementing, since this is the
#   riskiest call to get wrong (could skip the user's music unexpectedly).
