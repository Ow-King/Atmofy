# This file is responsible ONLY for producing an authenticated spotipy client.
# It should not contain the polling/recommendation loop -- that lives in
# app/services/playback_loop.py, which imports get_spotify_client() from here.
#
# TODO: wrap the block below in a get_spotify_client() function so callers
# (playback_loop.py, CLI commands, tests) can request a fresh/shared client
# instead of importing a module-level `sp` singleton.
#
# TODO: decide on token cache behavior -- SpotifyOAuth writes a .cache file by
# default; confirm that path is gitignored (it is not the same as .env) and
# consider pointing it at data/ via the `cache_path` kwarg per the .md spec's
# data/ directory layout.

import os
import spotipy

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.environ["SPOTIPY_CLIENT_ID"],
                                               client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
                                               redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
                                               scope="user-read-currently-playing user-modify-playback-state"))