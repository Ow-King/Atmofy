# Thin read-only wrapper around the spotipy client (from app/spotify/auth.py).
# Goal: isolate all Spotify *read* calls behind this module so the rest of the
# app never calls `sp.<method>` directly -- per the .md spec's constraint to
# keep Spotify calls behind a small client interface (so they can be mocked
# in tests or swapped if the API changes).
#
# TODO: get_current_playback(sp) -> dict | None
#   Wraps sp.current_user_playing_track(). Return None (not a raw Spotify
#   "nothing playing" shape) when the user isn't playing anything, so callers
#   in playback_loop.py can do a simple `if not playback:` check.
#
# TODO: get_current_playlist_id(sp) -> str | None
#   Spotify's currently-playing response includes a "context" object with the
#   playlist URI when playback started from a playlist. Extract/parse that
#   here. Return None if playing from an album/liked songs/queue (no
#   playlist context) -- playback_loop.py needs to handle that case too.
#
# TODO: get_playlist_tracks(sp, playlist_id) -> list[dict]
#   Wraps sp.playlist_items(), paginating past Spotify's 100-item page limit
#   (loop on the "next" field) so large playlists aren't silently truncated.
#   Return the minimal per-track shape the graph builder needs (track id,
#   name, artist id(s), position in playlist) rather than the full raw
#   Spotify payload.
#
# TODO: get_track_ids_only(sp, playlist_id) -> list[str]
#   Cheaper variant of the above for the common case where the loop just
#   needs to detect "has this playlist's tracklist changed" without pulling
#   full metadata every poll.
