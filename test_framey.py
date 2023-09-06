import importlib.resources
import os
import tempfile

import pytest
import requests
import requests_mock
from PIL import Image

from framey import Album, make_image, make_qrcode, make_html


@pytest.fixture
def album():
    return Album(
        cover="http://example.com/cover.jpeg",
        artist="Daniel Case",
        title="Engigstciak",
        year="2000",
        spotify_url="http://example.org",
        discogs_url="http://example.com",
        credits="By someone",
    )


def test_make_qrcode():
    with tempfile.TemporaryDirectory() as tmpdir:
        with importlib.resources.path("framey", "discogs.png") as image_path:
            filename = make_qrcode(
                "http://google.com/",
                embed_image=Image.open(image_path),
                color=(255, 255, 255),
                tmpdir=tmpdir,
            )
            assert os.path.getsize(os.path.join(tmpdir, filename)) > 1


def test_make_image(requests_mock, album):
    with importlib.resources.path("framey", "sample-cover.jpeg") as path:
        requests_mock.get(
            "http://example.com/cover.jpeg",
            body=open(path, "rb"),
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        image = make_image(make_html(album))
        assert image.size == (800, 480)
