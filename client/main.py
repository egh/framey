import gc

import inky_frame
import jpegdec
import machine
import sdcard
import uasyncio
import uos
import urequests
import WIFI_CONFIG
from network_manager import NetworkManager

# from picographics import PicoGraphics, DISPLAY_INKY_FRAME as DISPLAY      # 5.7"
# from picographics import PicoGraphics, DISPLAY_INKY_FRAME_4 as DISPLAY  # 4.0"
from picographics import DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"
from picographics import PicoGraphics

# Configure these
ENDPOINT = "http://retropie.local:5000/"
MAP = {inky_frame.button_a: "playing.jpeg", inky_frame.button_b: "weather.jpeg"}

# Default button
button = inky_frame.button_a


def mount_sd_card():
    print("mounting sd card")
    sd_spi = machine.SPI(
        0,
        sck=machine.Pin(18, machine.Pin.OUT),
        mosi=machine.Pin(19, machine.Pin.OUT),
        miso=machine.Pin(16, machine.Pin.OUT),
    )
    uos.mount(sdcard.SDCard(sd_spi, machine.Pin(22)), "/sd")


def build_headers():
    try:
        with open("etag", "r") as f:
            print("reading etag")
            etag = f.read()
            return {"If-None-Match": etag}
    except OSError:  # open failed
        return {}


def network_connect():
    print("connecting to network")
    network_manager = NetworkManager("GB")
    uasyncio.get_event_loop().run_until_complete(
        network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK)
    )


def read_jpeg(resp, filename):
    print("reading " + filename)
    socket = resp.raw
    # Stream the image data from the socket onto disk in 1024 byte chunks
    # the 600x448-ish jpeg will be roughly ~24k, we really don't have the RAM!
    data = bytearray(1024)
    with open(filename, "wb") as f:
        while True:
            if socket.readinto(data) == 0:
                break
            f.write(data)
    socket.close()


def display_jpeg(filename):
    print("displaying jpeg")
    graphics = PicoGraphics(DISPLAY)
    jpeg = jpegdec.JPEG(graphics)
    gc.collect()
    graphics.set_pen(1)
    graphics.clear()
    gc.collect()
    jpeg.open_file(filename)
    jpeg.decode(scale=False, dither=False)
    gc.collect()
    graphics.update()


def write_etag(resp):
    if "ETag" in resp.headers:
        print("writing etag")
        with open("etag", "w") as f:
            f.write(resp.headers["ETag"])


activity_led = machine.Pin(6, machine.Pin.OUT)
try:
    if inky_frame.button_a.read():
        button = inky_frame.button_a
    elif inky_frame.button_b.read():
        button = inky_frame.button_b
    elif inky_frame.button_c.read():
        button = inky_frame.button_c
    elif inky_frame.button_d.read():
        button = inky_frame.button_d
    elif inky_frame.button_e.read():
        button = inky_frame.button_e
    inky_frame.pcf_to_pico_rtc()
    activity_led.on()
    button.led_on()
    network_connect() and gc.collect()
    mount_sd_card() and gc.collect()
    image = MAP[button]
    filename = "/sd/" + image
    url = ENDPOINT + image
    print("requesting " + url)
    resp = urequests.get(url, headers=build_headers())
    if resp.status_code == 304:
        print("image unchanged")
    else:
        read_jpeg(resp, filename) and gc.collect()
        display_jpeg(filename) and gc.collect()
        write_etag(resp) and gc.collect()
    gc.collect()
except Exception as ex:
    print("Error: " + str(ex))
finally:
    activity_led.off()
    button.led_off()
    inky_frame.sleep_for(5)
