import importlib.resources
import os
import tempfile

import pytest
import requests
import requests_mock
from PIL import Image

from album_cards import Album, make_card, make_qrcode, make_card, make_html


@pytest.fixture
def album():
    return Album(
        cover="http://example.com/cover.jpeg",
        artist="Daniel Case",
        title="Engigstciak",
        year="2000",
        spotify_url="http://example.org",
        discogs_url="http://example.com",
    )


def test_make_qrcode():
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = make_qrcode(
            "http://google.com/",
            embed_image=Image.open(
                importlib.resources.files("album_cards").joinpath("discogs.png")
            ),
            color=(255, 255, 255),
            tmpdir=tmpdir,
        )
        assert os.path.getsize(os.path.join(tmpdir, filename)) > 1


def test_make_card(requests_mock, album):
    requests_mock.get(
        "http://example.com/cover.jpeg",
        body=open(
            importlib.resources.files("album_cards").joinpath("sample-cover.jpeg"), "rb"
        ),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        image = make_card(make_html(album))
        assert image.size == (600, 900)
