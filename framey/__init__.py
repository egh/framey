import os
import tempfile
from typing import Optional

import hitherdither
import qrcode
import qrcode.image.svg
from html2image import Html2Image
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask

USER_AGENT = "framey/0.1"
HEADERS = {
    "User-Agent": USER_AGENT,
}
HTI = Html2Image()


def make_qrcode(url: Optional[str], embed_image: Image, color: tuple, tmpdir) -> str:
    """Build a QRcode for a url with an optionally embedded image in
    the center and a given color. Will write image to the tmpdir and
    return the image file name."""
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


def render_image(html_dir: tempfile.TemporaryDirectory) -> Image:
    """Build a jpeg image from html. File will be dithered to work
    from inky frame colors, sized to 800x480. Directory should include
    a file named framey.html."""
    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False, dir=html_dir.name
    ) as tmp:
        HTI.output_path = html_dir.name
        HTI.screenshot(
            url="file:///" + os.path.join(html_dir.name, "index.html"),
            save_as=os.path.basename(tmp.name),
            size=(800, 480),
        )
        return Image.open(tmp.name)


def dither_image_path(path):
    """Dither an image file at path."""
    image = Image.open(path)
    dither_image_int(image).save(path)


def dither_image(image):
    """Dither an image."""
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
