import gc
import uos
import machine
import jpegdec
import uasyncio
import sdcard
import WIFI_CONFIG
import urequests
from network_manager import NetworkManager


# from picographics import PicoGraphics, DISPLAY_INKY_FRAME as DISPLAY      # 5.7"
# from picographics import PicoGraphics, DISPLAY_INKY_FRAME_4 as DISPLAY  # 4.0"
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"
import inky_frame

FILENAME = "/sd/playing.jpeg"
FILENAME_ETAG = FILENAME + "etag"
ENDPOINT = "http://retropie.local:5000/playing.jpeg"


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
        with open(FILENAME_ETAG, "r") as f:
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


def read_jpeg(resp):
    print("reading jpeg")
    socket = resp.raw
    # Stream the image data from the socket onto disk in 1024 byte chunks
    # the 600x448-ish jpeg will be roughly ~24k, we really don't have the RAM!
    data = bytearray(1024)
    with open(FILENAME, "wb") as f:
        while True:
            if socket.readinto(data) == 0:
                break
            f.write(data)
    socket.close()


def display_jpeg():
    print("displaying jpeg")
    graphics = PicoGraphics(DISPLAY)
    jpeg = jpegdec.JPEG(graphics)
    gc.collect()
    graphics.set_pen(1)
    graphics.clear()
    gc.collect()
    jpeg.open_file(FILENAME)
    jpeg.decode(scale=False, dither=False)
    gc.collect()
    graphics.update()


def write_etag(resp):
    if "ETag" in resp.headers:
        print("writing etag")
        with open(FILENAME + "etag", "w") as f:
            f.write(resp.headers["ETag"])


activity_led = machine.Pin(6, machine.Pin.OUT)

try:
    inky_frame.pcf_to_pico_rtc()
    activity_led.on()
    network_connect() and gc.collect()
    mount_sd_card() and gc.collect()
    print("getting image")
    resp = urequests.get(ENDPOINT, headers=build_headers())
    if resp.status_code == 304:
        print("image unchanged")
    else:
        read_jpeg(resp) and gc.collect()
        display_jpeg() and gc.collect()
        write_etag(resp) and gc.collect()
    gc.collect()
except Exception as ex:
    print(ex)
finally:
    activity_led.off()
    inky_frame.sleep_for(5)
