# This file is responsible ONLY for producing an authenticated spotipy client.
import os
import spotipy

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_client():
    load_dotenv()

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.environ["SPOTIPY_CLIENT_ID"],
                                                    client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
                                                    redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
                                                    scope="user-read-currently-playing user-modify-playback-state"))