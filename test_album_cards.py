import os
import tempfile
import pytest
import requests
import requests_mock

from album_cards import make_qrcode, render_html, make_card


def test_make_qrcode():
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = make_qrcode("http://google.com/", tmpdir=tmpdir)
        assert os.path.getsize(filename) > 1


def test_render_html():
    with tempfile.TemporaryDirectory() as tmpdir:
        image = render_html(
            tmpdir, "John Doe", "Untitled", "1999", "http://example.org"
        )
        assert image.size == (550, 250)


def test_make_card(requests_mock):
    requests_mock.get(
        "http://example.com/cover.jpeg", body=open("test_data/cover.jpeg", "rb")
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        image = make_card(
            "http://example.com/cover.jpeg",
            "Daniel Case",
            "Engigstciak",
            "2000",
            "http://example.org",
        )
        assert image.size == (600, 900)
