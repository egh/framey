import importlib.resources
import os
import tempfile
from dataclasses import dataclass

from typing import Optional, Union
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

DISCOGS_CLIENT = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))
SPOTIFY_CLIENT = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))


@dataclass
class Album:
    title: str
    artist: str
    year: str
    spotify_url: Optional[str]
    discogs_url: Optional[str]
    cover: Union[str, Image.Image]


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
        if type(album.cover) == str:
            req = requests.get(album.cover, headers=HEADERS, stream=True)
            req.raise_for_status()
            img = Image.open(req.raw)
        else:
            img = album.cover
        img = img.resize((550, 550))
        out = Image.new(mode=img.mode, size=(600, 900), color="white")
        out.paste(img, (25, 25))
        imgtext = render_html(tmpdir, album)
        out.paste(imgtext, (25, 625), mask=imgtext)
        return out


def make_spotify_album(item) -> Album:
    return Album(
        cover=item["images"][0]["url"],
        artist=", ".join([artist["name"] for artist in item["artists"]]),
        title=item["name"],
        year=item["release_date"][0:4],
        spotify_url=item["external_urls"]["spotify"],
        discogs_url=None,
    )


def make_discogs_album(release) -> Album:
    return Album(
        cover=release.images[0]["uri"],
        artist=release.artists_sort,
        title=release.title,
        year=release.year,
        discogs_url=release.url,
        spotify_url=None,
    )


def get_spotify_url(album):
    results = SPOTIFY_CLIENT.search(
        q=f"artist:{album.artist} album:{album.title}", type="album"
    )["albums"]["items"]
    if len(results) == 0:
        return None
    return results[0]["external_urls"]["spotify"]


def get_discogs_url(album):
    results = DISCOGS_CLIENT.search(album.title, artist=album.artist, type="master")
    if len(results) == 0:
        return None
    return f"https://www.discogs.com{results[0].url}"


def make_spotify_cards():
    results = SPOTIFY_CLIENT.current_user_saved_albums()
    albums = results["items"]
    while results["next"]:
        results = SPOTIFY_CLIENT.next(results)
        albums.extend(results["items"])

    for item in albums:
        album = make_spotify_album(item["album"])
        album.discogs_url = get_discogs_url(album)
        make_card(album).save(f"{item['album']['id']}.jpeg")


def make_discogs_cards():
    for item in DISCOGS_CLIENT.identity().collection_folders[0].releases:
        album = make_discogs_album(item.release)
        album.spotify_url = get_spotify_url(album)
        make_card(album).save(f"{item.release.id}.jpeg")
