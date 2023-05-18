import tempfile
from framey import make_now_playing_card
from flask import Flask, make_response, send_file

app = Flask(__name__)


@app.route("/playing.jpeg")
def now_playing():
    tmpfile = tempfile.TemporaryFile(suffix=".jpeg")
    make_now_playing_card().convert("RGB").save(tmpfile, format="JPEG")
    tmpfile.seek(0)
    return send_file(tmpfile, mimetype="application/jpeg")
