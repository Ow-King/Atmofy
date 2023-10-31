class Atmofy:
    def __init__(self, sp):
        self.sp = sp;


    def get_current_song(self):
        # Get track information
        track = self.sp.current_user_playing_track()
        artist = track["item"]["artists"][0]["name"]
        t_name = track["item"]["name"]
        t_id = track["item"]["id"]
        return artist, t_name, t_id

    def print_current_song(self):
        artist, track, tid = self.get_current_song()
        if artist !="":
            print(f"Currently playing {artist} - {track} - {tid}")

    def get_track_features(self, id):
        metadata = self.sp.track(id)
        features = self.sp.audio_features(id)

        # metadata
        name = metadata['name']
        album = metadata['album']['name']
        artist = metadata['album']['artists'][0]['name']
        release_date = metadata['album']['release_date']
        length = metadata['duration_ms']
        popularity = metadata['popularity']

        # audio features
        acousticness = features[0]['acousticness']
        danceability = features[0]['danceability']
        energy = features[0]['energy']
        instrumentalness = features[0]['instrumentalness']
        liveness = features[0]['liveness']
        loudness = features[0]['loudness']
        speechiness = features[0]['speechiness']
        tempo = features[0]['tempo']
        time_signature = features[0]['time_signature']

        track = [name, album, artist, release_date, length, popularity, danceability, acousticness, danceability, energy, instrumentalness, liveness, loudness, speechiness, tempo, time_signature, id]
        return track


    def playlist_tracks(self, playlist_id):
        tracks = self.sp.playlist_items(playlist_id, ['id'], 100, 0, "US", "track")

    def store_current_song(self, file_name, song_id, time):
        f = open(file_name, "a")
        f.write(str(time))
        f.write("\n")
        f.write(self.get_track_features(song_id)[16])
        f.write(" ")
        f.close()

    def check_song_change(self, file_name, song_id):
        f = open(file_name, "r")

        # Get the ID of the last song from the file and the id of the current song
        lastAddedSong = f.readlines()[len(f.readlines()) - 1].split(" ")[0]
        currentSong = self.get_track_features(song_id)[16]
        print(lastAddedSong)
        print(currentSong)

        f.close()

        if (lastAddedSong != currentSong):
            return True
        return False