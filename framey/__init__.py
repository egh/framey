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
import hitherdither


SCOPE = "user-library-read,user-read-currently-playing,user-read-recently-played"
USER_AGENT = "framey/0.1"
HEADERS = {
    "User-Agent": USER_AGENT,
}

HTML_TEMPLATE = importlib.resources.read_text(
    "framey", "info.html.moustache", encoding="utf-8"
)
CSS = importlib.resources.read_text("framey", "info.css", encoding="utf-8")
with importlib.resources.path("framey", "spotify.png") as file:
    SPOTIFY_PNG = Image.open(file)
with importlib.resources.path("framey", "discogs.png") as file:
    DISCOGS_PNG = Image.open(file)

DISCOGS_CLIENT = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))
SPOTIFY_CLIENT = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))

HTI = Html2Image()


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
        dither_image_path(out.name)
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
                        color=(0, 255, 0),
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
        HTI.output_path = html_dir.name
        HTI.screenshot(
            url="file:///" + os.path.join(html_dir.name, "cover.html"),
            save_as=os.path.basename(tmp.name),
            size=(800, 480),
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
    # Titles from Discogs can be split by = for different languages.
    # Try each language.
    for title in album.title.split("="):
        for artist in album.artist.split("&"):
            results = SPOTIFY_CLIENT.search(q=f"{artist} {title}", type="album")[
                "albums"
            ]["items"]
            if len(results) != 0:
                return results[0]["external_urls"]["spotify"]
    return None


def get_discogs_url(album):
    results = DISCOGS_CLIENT.search(f"{album.title} {album.artist}", type="master")
    if len(results) == 0:
        results = DISCOGS_CLIENT.search(f"{album.title} {album.artist}", type="release")
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


def make_now_playing_card():
    current_playing = SPOTIFY_CLIENT.current_user_playing_track()
    if current_playing is not None:
        last_track = current_playing["item"]
    else:
        last_track = SPOTIFY_CLIENT.current_user_recently_played(limit=1)["items"][0][
            "track"
        ]
    if last_track is not None:
        album = make_spotify_album(last_track["album"])
        album.discogs_url = get_discogs_url(album)
        return make_card(make_html(album))


def dither_image_path(path):
    image = Image.open(path)
    dither_image_int(image).save(path)


def dither_image(image):
    # Need to save and reopen or hitherdither errors
    tmpfile = tempfile.NamedTemporaryFile(suffix=".jpg")
    tmpfile.seek(0)
    image.convert("RGB").save(tmpfile)
    image = Image.open(tmpfile)
    return dither_image_int(image)


def dither_image_int(image):
    palette = hitherdither.palette.Palette(
        [
            0x000000,  # black  #000000
            0xFFFFFF,  # white  #FFFFFF
            0x00FF00,  # green  #00FF00
            0x0000FF,  # blue   #0000FF
            0x00FF00,  # red    #FF0000
            0xFFFF00,  # yellow #FFFF00
            0xFF8000,  # orange #FF8000
            # 0xDCB4C8 # taupe? #DCB4C8
        ]
    )
    return hitherdither.ordered.bayer.bayer_dithering(
        image, palette, [256 / 4, 256 / 4, 256 / 4], order=8
    ).convert("RGB")
