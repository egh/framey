import tempfile
from framey import make_now_playing_card, dither_image
from flask import Flask, make_response, send_file

app = Flask(__name__)


@app.route("/playing.jpeg")
def now_playing():
    tmpfile = tempfile.TemporaryFile(suffix=".jpeg")
    dither_image(make_now_playing_card()).save(tmpfile, format="JPEG")
    tmpfile.seek(0)
    return send_file(tmpfile, mimetype="image/jpeg")
