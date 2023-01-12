import importlib.resources

from PIL import Image

from album_cards import make_card, Album


make_card(
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
).save("sample.jpeg")
