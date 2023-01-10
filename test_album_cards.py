import os
import tempfile
import pytest
import requests
import requests_mock

from album_cards import make_qrcode, render_html, make_card, Album


@pytest.fixture
def album():
    return Album(
        cover_url="http://example.com/cover.jpeg",
        artist="Daniel Case",
        title="Engigstciak",
        year="2000",
        qr_url="http://example.org",
    )


def test_make_qrcode():
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = make_qrcode("http://google.com/", tmpdir=tmpdir)
        assert os.path.getsize(filename) > 1


def test_render_html(album):
    with tempfile.TemporaryDirectory() as tmpdir:
        image = render_html(tmpdir, album)
        assert image.size == (550, 250)


def test_make_card(requests_mock, album):
    requests_mock.get(
        "http://example.com/cover.jpeg", body=open("test_data/cover.jpeg", "rb")
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        image = make_card(album)
        assert image.size == (600, 900)
