import os
import tempfile

import chevron
import importlib.resources
import qrcode
import qrcode.image.svg
import requests
from html2image import Html2Image
from PIL import Image

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


def make_qrcode(url: str, tmpdir) -> str:
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, dir=tmpdir) as out:
        img.save(out)
        return out.name


def render_html(tmpdir, artist, album, year, qr_url) -> Image:
    """Load a textual resource file."""

    hti = Html2Image()
    hti.output_path = tmpdir
    qrcode_file = make_qrcode(qr_url, tmpdir=tmpdir)
    html = chevron.render(
        HTML_TEMPLATE,
        {"year": year, "album": album, "artist": artist, "qrcode": qrcode_file},
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=tmpdir) as tmp:
        hti.screenshot(
            html_str=html,
            css_str=CSS,
            save_as=os.path.basename(tmp.name),
            size=(550, 250),
        )
        return Image.open(tmp.name)


def make_card(cover_url, artist, album, year, qr_url) -> Image:
    with tempfile.TemporaryDirectory() as tmpdir:
        req = requests.get(cover_url, headers=HEADERS, stream=True)
        req.raise_for_status()
        img = Image.open(req.raw)
        img = img.resize((600, 600))
        out = Image.new(mode=img.mode, size=(600, 900), color="white")
        out.paste(img)
        imgtext = render_html(tmpdir, artist, album, year, qr_url)
        out.paste(imgtext, (25, 625), mask=imgtext)
        return out
