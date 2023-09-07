import tempfile
from zlib import adler32

import spotipy
from flask import Flask, make_response, request, send_file
from spotipy.oauth2 import SpotifyOAuth
from werkzeug.utils import send_file

from framey import dither_image
from framey.spotify import make_now_playing_image

SCOPE = "user-library-read,user-read-currently-playing,user-read-recently-played"

app = Flask(__name__)


@app.route("/playing.jpeg")
def now_playing():
    spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
    tmpfile = tempfile.NamedTemporaryFile(suffix=".jpeg")
    make_now_playing_image(spotify_client).convert("RGB").save(tmpfile, format="JPEG")
    tmpfile.seek(0)
    etag = str(adler32(tmpfile.read()) & 0xFFFFFFFF)
    tmpfile.seek(0)
    return send_file(tmpfile, request.environ, mimetype="image/jpeg", etag=etag)
