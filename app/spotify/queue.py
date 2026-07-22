# Thin write-only wrapper around the spotipy client (from app/spotify/auth.py).
# Counterpart to client.py -- everything here mutates Spotify playback state,
# so keep these calls isolated and easy to mock/no-op in tests (you do not
# want tests accidentally skipping the user's real music).

import spotipy
import time

from app.spotify.auth import get_spotify_client
from app.spotify.client import get_current_playback

#   Wraps sp.add_to_queue(track_uri). This is the "add one recommended song"
#   primitive that recommendation_service.py's output feeds into.
def queue_track(sp, track_uri) -> None:
    sp.add_to_queue(track_uri)


#   Convenience loop over queue_track for topping up the 3-song buffer in
#   one call from playback_loop.py.
def queue_tracks(sp, tracks_uris) -> None:
    for uri in tracks_uris:
        queue_track(sp, uri)


#   Wraps sp.next_track(). Used when playback_loop.py detects the playlist
#   changed and needs to move off whatever Spotify auto-queued.
def skip_to_next(sp) -> None:
    sp.next_track()


# clear_queue(sp, queued_track_ids) -> None
#   Spotify's API has no direct "clear queue" endpoint, and skipping the
#   moment a playlist change is detected would cut off the song the user
#   picked on the new playlist. Instead, wait until the current song ends,
#   then compare the front of the live queue against queued_track_ids (the
#   stale recommendations added while the old playlist was active). Only
#   skip past however many of those still sit unchanged at the front, if
#   the user has already skipped/reordered, the comparison stops matching
#   and leave the rest of the queue alone.
def clear_queue(sp, queued_track_ids) -> None:
    # Find out how long is left on the current song
    playback = get_current_playback(sp)

    if not playback:
        print("Nothing Playing")
        return

    # Wait untill the end of the song to skip the queue
    duration = playback["item"]["duration_ms"]
    runtime = playback["progress_ms"]
    ms_remaining = duration - runtime
    print(f"Duration: {duration}")
    print(f"Runtime: {runtime}")
    print(f"ms_remaining: {ms_remaining}")
    time.sleep(ms_remaining / 1000)
    print("Skipping Queue Now")

    # Check to make sure the user didnt skip the song
    playback = get_current_playback(sp)
    if not playback:
        print("Nothing Playing")
        return
    runtime = playback["progress_ms"]

    if runtime > 1000: # Over a second means that the song was likely skipped
        return

    # Check the status of the queue and check the ids of the upcoming queued items
    queue_state = sp.queue()
    upcoming_ids = [track["id"] for track in queue_state.get("queue", [])]

    # Only count the stale tracks still sitting untouched at the front of
    # the queue stop at the first mismatch, since that means the user
    # has already skipped or otherwise changed the queue themselves.
    stale_count = 0
    for expected_id, actual_id in zip(queued_track_ids, upcoming_ids):
        if expected_id != actual_id:
            break
        stale_count += 1

    print(f"Skipping {stale_count} stale queued track(s)")
    for _ in range(stale_count):
        skip_to_next(sp)


if __name__ == "__main__":
    sp = get_spotify_client()
    # queue_track(sp, track_uri)
    # queue_tracks(sp, tracks_uris)
    # skip_to_next(sp)
    # clear_queue(sp, [])


