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


def make_qrcode(url: Optional[str], embed_image: Image, color: tuple, tmpdir) -> str:
    if url is None:
        return ""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    qr.add_data(url)
    img = qr.make_image(
        image_factory=StyledPilImage,
        embeded_image=embed_image,
        color_mask=SolidFillColorMask(front_color=color),
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=tmpdir) as out:
        img.save(out)
        return os.path.basename(out.name)


def download_cover(tmpdir, album) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=tmpdir) as out:
        if isinstance(album.cover, str):
            resp = requests.get(album.cover, headers=HEADERS, stream=True)
            resp.raise_for_status()
            out.write(resp.content)
        else:
            album.cover.save(out)
        return os.path.basename(out.name)


def make_html(album: Album) -> tempfile.TemporaryDirectory():
    tmpdir = tempfile.TemporaryDirectory()
    with open(os.path.join(tmpdir.name, "cover.html"), "w") as f:
        f.write(
            chevron.render(
                HTML_TEMPLATE,
                {
                    "cover": download_cover(tmpdir.name, album),
                    "year": album.year,
                    "title": album.title,
                    "artist": album.artist,
                    "spotify_qrcode": make_qrcode(
                        album.spotify_url,
                        embed_image=SPOTIFY_PNG,
                        color=(46, 189, 89),
                        tmpdir=tmpdir.name,
                    ),
                    "discogs_qrcode": make_qrcode(
                        album.discogs_url,
                        embed_image=DISCOGS_PNG,
                        color=(0, 0, 0),
                        tmpdir=tmpdir.name,
                    ),
                },
            )
        )
    with open(os.path.join(tmpdir.name, "cover.css"), "w") as f:
        f.write(CSS)
    return tmpdir


def make_card(html_dir: tempfile.TemporaryDirectory) -> Image:
    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False, dir=html_dir.name
    ) as tmp:
        hti = Html2Image()
        hti.output_path = html_dir.name
        hti.screenshot(
            url="file:///" + os.path.join(html_dir.name, "cover.html"),
            save_as=os.path.basename(tmp.name),
            size=(600, 900),
        )
        return Image.open(tmp.name)


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
        make_card(make_html(album)).save(f"{item['album']['id']}.png")


def make_discogs_cards():
    for item in DISCOGS_CLIENT.identity().collection_folders[0].releases:
        album = make_discogs_album(item.release)
        album.spotify_url = get_spotify_url(album)
        make_card(make_html(album)).save(f"{item.release.id}.png")
