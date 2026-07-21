import pandas as pd
import spotipy
import time

from numpy.matlib import rand
from spotipy.oauth2 import SpotifyOAuth

from legacy_app.Atmofy import Atmofy
from legacy_app.Location import Location

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="e3bb8bebeef74fc3804af340240c5dc1",
                                               client_secret="361486dd53494e33b5b988933db14e72",
                                               redirect_uri="http://localhost:1234",
                                               scope="user-read-currently-playing user-modify-playback-state"))

def main():
    # Take in user input of desired playlist and curent zip code
    print("Enter Playlist URL:")
    # playlist_link = input()
    playlist_link = "https://open.spotify.com/playlist/37i9dQZF1DZ06evO3Q3rMI?si=34c0ec5e8a534c87"
    print("Enter Current Zip Code:")
    zipCode = input()

    weather = Location(zipCode)
    user = Atmofy(sp)

    temp, weekday, sky = weather.getWeather

    # Takes the URI of the playlist and turns it into a DataFrame of Attributes to be accessed for cosine similarity
    playlist_URI = playlist_link.split("/")[-1].split("?")[0]
    track_uris = [x["track"]["uri"] for x in sp.playlist_tracks(playlist_URI)["items"]]
    tracks = []


    #   for i in range(len(track_uris)):
    #       track = user.get_track_features(track_uris[i])
    #       tracks.append(track)
    #   df = pd.DataFrame(tracks,
    #                     columns=['name', 'album', 'artist', 'release_date', 'length', 'popularity', 'danceability',
    #                              'acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness',
    #                              'speechiness', 'tempo', 'time_signature', 'URI'])
    #   print(df.to_string())
    #   sp.add_to_queue(str(df.get('URI')[2]))

    fileName = weather.getTime()

    artist, track, tid = user.get_current_song()
    user.store_current_song(fileName, tid, 0)

    # Every 3 seconds check to see if the song has changed, if so store the new song ID into the file
    timePlayed = time.time();
    timePlayed = int(timePlayed * 1000)

    while True:
        artist, track, tid = user.get_current_song()
        if (user.check_song_change(fileName, tid)):
            user.store_current_song(fileName, tid, int(time.time() * 1000) - timePlayed)
            print("NEW SONG DETECTED AND STORED")

            # Update Current Time
            fileName = weather.getTime()

            # Reset timer on how long song was played
            timePlayed = time.time();
            timePlayed = int(timePlayed * 1000)
        else:
            print("NO CHANGE IN SONG")

            # Song has been playing for 3000 miliseconds
            timePlayed += 3000
        time.sleep(3)

if __name__ == '__main__':
    main()