import importlib.resources
import os
import shutil

from PIL import Image

from framey import Album, make_image, make_html

html_dir = make_html(
    Album(
        cover=Image.open(
            importlib.resources.files("framey").joinpath("sample-cover.jpeg")
        ),
        artist="Aliquam erat volutpat.  Nunc eleifend leo vitae magna.  In id erat non orci commodo lobortis.  Proin neque massa, cursus ut, gravida ut, lobortis eget, lacus.  Sed diam.  Praesent fermentum tempor tellus.  Nullam tempus.",
        title="Mauris ac felis vel velit tristique imperdiet.  Donec at pede.  Etiam vel neque nec dui dignissim bibendum.",
        year="2016",
        spotify_url="https://spotify.com",
        discogs_url="https://discogs.com",
    )
)

make_image(html_dir).save("sample.png")
if os.path.isdir("sample"):
    shutil.rmtree("sample")
shutil.copytree(html_dir.name, "sample")
