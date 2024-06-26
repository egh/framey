import tempfile
from zlib import adler32

import spotipy
from flask import Flask, make_response, request, send_file
from spotipy.oauth2 import SpotifyOAuth
from werkzeug.utils import send_file

from framey import dither_image
from framey.spotify import make_now_playing_image
from framey.weather import make_weather_image

SCOPE = "user-library-read,user-read-currently-playing,user-read-recently-played"

app = Flask(__name__)

# Force login if not cached.
spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE)).current_user()


def serve_image(image):
    tmpfile = tempfile.NamedTemporaryFile(suffix=".jpeg")
    image = image.convert("RGB")
    image = dither_image(image)
    image.save(tmpfile, format="JPEG")
    tmpfile.seek(0)
    etag = str(adler32(tmpfile.read()) & 0xFFFFFFFF)
    tmpfile.seek(0)
    return send_file(tmpfile, request.environ, mimetype="image/jpeg", etag=etag)


@app.route("/playing.jpeg")
def now_playing():
    spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
    return serve_image(make_now_playing_image(spotify_client))


@app.route("/weather.jpeg")
def weather():
    return serve_image(make_weather_image())
