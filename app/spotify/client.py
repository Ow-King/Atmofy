# Thin read-only wrapper around the spotipy client (from app/spotify/auth.py).
# Goal: isolate all Spotify *read* calls behind this module so the rest of the
# app never calls `sp.<method>` directly -- per the .md spec's constraint to
# keep Spotify calls behind a small client interface (so they can be mocked
# in tests or swapped if the API changes).

import spotipy

from app.spotify.auth import get_spotify_client

#   get_current_playback(sp) -> dict | None
#   Wraps sp.current_user_playing_track(). Return None (not a raw Spotify
#   "nothing playing" shape) when the user isn't playing anything, so callers
#   in playback_loop.py can do a simple `if not playback:` check.
def get_current_playback(sp) -> dict | None:
    track_playing = sp.current_user_playing_track()
    if track_playing["is_playing"]:
        return track_playing
    return False


#   get_current_playlist_id(sp) -> str | None
#   Spotify's currently-playing response includes a "context" object with the
#   playlist URI when playback started from a playlist. Extract/parse that
#   here. Return None if playing from an album/liked songs/queue (no
#   playlist context) -- playback_loop.py needs to handle that case too.
def get_current_playlist_id(sp) -> str | None:
    track_playing = sp.current_user_playing_track()
    if track_playing["context"]:
        return track_playing["context"]["uri"] # Give back the playlist ID for comparison
    return False # This is if they are playing from an artist, or a non-structured album


#   get_playlist_tracks(sp, playlist_id) -> list[dict]
#   Wraps sp.playlist_items(), paginating past Spotify's 100-item page limit
#   (loop on the "next" field) so large playlists aren't silently truncated.
#   Return the minimal per-track shape the graph builder needs (track id,
#   name, artist id(s), position in playlist) rather than the full raw
#   Spotify payload.
def get_playlist_tracks(sp, playlist_id) -> list[dict]:
    if playlist_id is None:
        return None
    current_playlist = sp.playlist_items(playlist_id)
    return current_playlist


#   get_track_ids_only(sp, playlist_id) -> list[str]
#   Cheaper variant of the above for the common case where the loop just
#   needs to detect "has this playlist's tracklist changed" without pulling
#   full metadata every poll.
def get_track_ids_only(sp, playlist_id) -> list[str]:
    if playlist_id is None:
        return []

    track_ids = []
    results = sp.playlist_items(playlist_id, fields="items.item.id,items.item.track,next")
    while results:
        track_ids.extend(
            entry["item"]["id"]
            for entry in results["items"]
            if entry.get("item") and entry["item"].get("track")
        )
        results = sp.next(results) if results.get("next") else None

    return track_ids


if __name__ == "__main__":
    sp = get_spotify_client()
    playback = get_current_playback(sp)
    playlist = get_current_playlist_id(sp)
    tracks = get_playlist_tracks(sp, playlist)
    track_ids = get_track_ids_only(sp, playlist)
    print("\nPlayback:")
    print(playback)
    print("\nPlaylist:")
    print(playlist)
    print("\nTracks:")
    print(tracks)
    print("\nTrack IDs:")
    print(track_ids)
