import importlib.resources
import os
import tempfile
from dataclasses import dataclass

from typing import Optional
import chevron
import discogs_client
import qrcode
import qrcode.image.svg
import requests
import spotipy
from html2image import Html2Image
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
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
SPOTIFY_PNG = Image.open(
    importlib.resources.files("album_cards").joinpath("spotify.png")
)
DISCOGS_PNG = Image.open(
    importlib.resources.files("album_cards").joinpath("discogs.png")
)


@dataclass
class Album:
    title: str
    artist: str
    year: str
    spotify_url: Optional[str]
    discogs_url: Optional[str]
    cover_url: str


def make_qrcode(url: str, embed_image: Image, color: tuple, tmpdir) -> str:
    if url is None:
        return ""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(url)
    img = qr.make_image(
        image_factory=StyledPilImage,
        embeded_image=embed_image,
        color_mask=SolidFillColorMask(front_color=color),
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=tmpdir) as out:
        img.save(out)
        return out.name


def render_html(tmpdir, album: Album) -> Image:
    hti = Html2Image()
    hti.output_path = tmpdir
    html = chevron.render(
        HTML_TEMPLATE,
        {
            "year": album.year,
            "title": album.title,
            "artist": album.artist,
            "spotify_qrcode": make_qrcode(
                album.spotify_url,
                embed_image=SPOTIFY_PNG,
                color=(46, 189, 89),
                tmpdir=tmpdir,
            ),
            "discogs_qrcode": make_qrcode(
                album.discogs_url,
                embed_image=DISCOGS_PNG,
                color=(0, 0, 0),
                tmpdir=tmpdir,
            ),
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
            spotify_url=album["external_urls"]["spotify"],
            discogs_url=None,
        )
    )


def make_card_discogs(release) -> Image:
    return make_card(
        Album(
            cover_url=release.images[0]["uri"],
            artist=release.artists_sort,
            title=release.title,
            year=release.year,
            discogs_url=release.url,
            spotify_url=None,
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
