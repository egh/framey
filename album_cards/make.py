import os
import tempfile

import chevron
import discogs_client
import requests
import spotipy
from html2image import Html2Image
from PIL import Image
from PIL.ExifTags import Base
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


USER_AGENT = "album_cards/0.1"
HEADERS = {
    "User-Agent": USER_AGENT,
}
CSS = """
* { font-family: "Noto Sans"; font-size: 20pt }
"""

HTML = """
<i>{{album}}</i>
{{#year}}
({{year}})
{{/year}}
<br>
<br>
{{artist}}
"""

TEXT = """
{{album}}
{{#year}}
({{year}})
{{/year}} / {{artist}}
"""

SCOPE = "user-library-read"


def make_image_from_url(url, output, hti, artist, album, year):
    r = requests.get(url, headers=HEADERS, stream=True)
    r.raise_for_status()
    img = Image.open(r.raw)
    img = img.resize((600, 600))
    out = Image.new(mode=img.mode, size=(600, 900), color="white")
    out.paste(img)
    textf = f"{output}_text.png"
    md = {"year": year, "album": album, "artist": artist}
    html = chevron.render(HTML, md)
    text = chevron.render(TEXT, md)
    hti.screenshot(html_str=html, css_str=CSS, save_as=textf, size=(550, 250))
    imgtext = Image.open(os.path.join(tmpdir, textf))
    out.paste(imgtext, (25, 625), mask=imgtext)
    exif = img.getexif()
    exif[Base.ImageDescription.value] = text
    out.save(output, exif=exif)


with tempfile.TemporaryDirectory() as tmpdir:
    hti = Html2Image()
    hti.output_path = tmpdir

    d = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))
    me = d.identity()
    for item in me.collection_folders[0].releases:
        release = item.release
        uri = release.images[0]["uri"]
        make_image_from_url(
            uri,
            f"{release.id}.jpeg",
            hti,
            release.artists_sort,
            release.title,
            release.year,
        )

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))

    results = sp.current_user_saved_albums()
    albums = results["items"]
    while results["next"]:
        results = sp.next(results)
        albums.extend(results["items"])

    for item in albums:
        album = item["album"]
        url = item["album"]["images"][0]["url"]
        title = album["name"]
        artist = ", ".join([artist["name"] for artist in album["artists"]])
        year = album["release_date"][0:4]
        make_image_from_url(url, f"{album['id']}.jpeg", hti, artist, title, year)
