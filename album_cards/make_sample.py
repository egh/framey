import importlib.resources
import shutil
from PIL import Image

from album_cards import make_card, Album, make_html

html_dir = make_html(
    Album(
        cover=Image.open(
            importlib.resources.files("album_cards").joinpath("sample-cover.jpeg")
        ),
        artist="Koenix",
        title="From Wikipedia",
        year="2016",
        spotify_url="https://spotify.com",
        discogs_url="https://discogs.com",
    )
)

make_card(html_dir).save("sample.png")
shutil.copytree(html_dir.name, "sample")
