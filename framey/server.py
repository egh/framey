import tempfile
from framey import make_now_playing_card, dither_image
from flask import Flask, make_response, send_file, request
from werkzeug.utils import send_file
from zlib import adler32

app = Flask(__name__)


@app.route("/playing.jpeg")
def now_playing():
    tmpfile = tempfile.NamedTemporaryFile(suffix=".jpeg")
    make_now_playing_card().convert("RGB").save(tmpfile, format="JPEG")
    tmpfile.seek(0)
    etag = str(adler32(tmpfile.read()) & 0xffffffff)
    tmpfile.seek(0)
    return send_file(tmpfile, request.environ, mimetype="image/jpeg",
                     etag=etag)
    
