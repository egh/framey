import importlib.resources
import os
import tempfile
from dataclasses import dataclass

import chevron
import discogs_client
import qrcode
import qrcode.image.svg
import requests
import spotipy
from html2image import Html2Image
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth

SCOPE = "user-library-read"
USER_AGENT = "album_cards/0.1"
HEADERS = {
    "User-Agent": USER_AGENT,
}

HTML_TEMPLATE = (
    importlib.resources.files("album_cards")
    .joinpath("info.html.moustache")
    .read_text(encoding="utf-8")
)
CSS = (
    importlib.resources.files("album_cards")
    .joinpath("info.css")
    .read_text(encoding="utf-8")
)


@dataclass
class Album:
    title: str
    artist: str
    year: str
    qr_url: str
    cover_url: str


def make_qrcode(url: str, tmpdir) -> str:
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, dir=tmpdir) as out:
        img.save(out)
        return out.name


def render_html(tmpdir, album: Album) -> Image:
    hti = Html2Image()
    hti.output_path = tmpdir
    qrcode_file = make_qrcode(album.qr_url, tmpdir=tmpdir)
    html = chevron.render(
        HTML_TEMPLATE,
        {
            "year": album.year,
            "title": album.title,
            "artist": album.artist,
            "qrcode": qrcode_file,
        },
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=tmpdir) as tmp:
        hti.screenshot(
            html_str=html,
            css_str=CSS,
            save_as=os.path.basename(tmp.name),
            size=(550, 250),
        )
        return Image.open(tmp.name)


def make_card(album: Album) -> Image:
    with tempfile.TemporaryDirectory() as tmpdir:
        req = requests.get(album.cover_url, headers=HEADERS, stream=True)
        req.raise_for_status()
        img = Image.open(req.raw)
        img = img.resize((600, 600))
        out = Image.new(mode=img.mode, size=(600, 900), color="white")
        out.paste(img)
        imgtext = render_html(tmpdir, album)
        out.paste(imgtext, (25, 625), mask=imgtext)
        return out


def make_card_spotify(album) -> Image:
    return make_card(
        Album(
            cover_url=album["images"][0]["url"],
            artist=", ".join([artist["name"] for artist in album["artists"]]),
            title=album["name"],
            year=album["release_date"][0:4],
            qr_url=album["external_urls"]["spotify"],
        )
    )


def make_card_discogs(release) -> Image:
    return make_card(
        Album(
            cover_url=release.images[0]["uri"],
            artist=release.artists_sort,
            title=release.title,
            year=release.year,
            qr_url=release.url,
        )
    )


def make_spotify_cards():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
    results = sp.current_user_saved_albums()
    albums = results["items"]
    while results["next"]:
        results = sp.next(results)
        albums.extend(results["items"])

    for item in albums:
        make_card_spotify(item["album"]).save(f"{item['album']['id']}.jpeg")


def make_discogs_cards():
    d = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))
    me = d.identity()
    for item in me.collection_folders[0].releases:
        make_card_discogs(item.release).save(f"{item.release.id}.jpeg")
