import importlib.resources
import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Union

import chevron
import discogs_client
import requests
from PIL import Image

from framey import (
    HEADERS,
    USER_AGENT,
    dither_image_path,
    render_image,
    make_qrcode,
)

HTML_TEMPLATE = importlib.resources.read_text(
    "framey", "info.html.moustache", encoding="utf-8"
)
CSS = importlib.resources.read_text("framey", "info.css", encoding="utf-8")
with importlib.resources.path("framey", "spotify.png") as file:
    SPOTIFY_PNG = Image.open(file)
with importlib.resources.path("framey", "discogs.png") as file:
    DISCOGS_PNG = Image.open(file)

DISCOGS_CLIENT = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))


@dataclass
class Album:
    title: str
    artist: str
    year: str
    spotify_url: Optional[str]
    discogs_url: Optional[str]
    cover: Union[str, Image.Image]
    credits: Optional[str]


def make_spotify_album(item) -> Album:
    return Album(
        cover=item["images"][0]["url"],
        artist=", ".join([artist["name"] for artist in item["artists"]]),
        title=item["name"],
        year=item["release_date"][0:4],
        spotify_url=item["external_urls"]["spotify"],
        discogs_url=None,
        credits=None,
    )


def discogs_enhance(album):
    results = DISCOGS_CLIENT.search(f"{album.title} {album.artist}", type="master")
    if len(results) > 0:
        credits = results[0].main_release.credits
        url = results[0].url
    else:
        results = DISCOGS_CLIENT.search(f"{album.title} {album.artist}", type="release")
        if len(results) > 0:
            credits = results[0].credits
            url = results[0].url
        else:
            return
    album.credits = credits
    album.discogs_url = url


def make_now_playing_image(spotify_client):
    current_playing = spotify_client.current_user_playing_track()
    if current_playing is not None:
        last_track = current_playing["item"]
    else:
        last_track = spotify_client.current_user_recently_played(limit=1)["items"][0][
            "track"
        ]
    if last_track is not None:
        album = make_spotify_album(last_track["album"])
        discogs_enhance(album)
        return render_image(make_html(album))


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
    with open(os.path.join(tmpdir.name, "index.html"), "w") as f:
        f.write(
            chevron.render(
                HTML_TEMPLATE,
                {
                    "cover": download_cover(tmpdir.name, album),
                    "year": album.year,
                    "title": album.title,
                    "artist": album.artist,
                    "credits": album.credits,
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
