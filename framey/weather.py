# From https://github.com/Dachaz/inky-weatherbox

import requests
import json
import tempfile
import os
import chevron
from framey import render_image
import importlib
import shutil

HTML_TEMPLATE = importlib.resources.read_text(
    "framey", "weather.html.moustache", encoding="utf-8"
)

# https://gist.githubusercontent.com/stellasphere/9490c195ed2b53c707087c8c2db4ec0c/raw/7f2d37310ac5d5c309fd9d2f4dd98cc837c28237/descriptions.json
CODES = {
    0: {
        "day": ("Sunny", "http://openweathermap.org/img/wn/01d@2x.png"),
        "night": ("Clear", "http://openweathermap.org/img/wn/01n@2x.png"),
    },
    1: {
        "day": ("Mainly Sunny", "http://openweathermap.org/img/wn/01d@2x.png"),
        "night": (
            "Mainly Clear",
            "http://openweathermap.org/img/wn/01n@2x.png",
        ),
    },
    2: {
        "day": ("Partly Cloudy", "http://openweathermap.org/img/wn/02d@2x.png"),
        "night": ("Partly Cloudy", "http://openweathermap.org/img/wn/02n@2x.png"),
    },
    3: {
        "day": ("Cloudy", "http://openweathermap.org/img/wn/03d@2x.png"),
        "night": ("Cloudy", "http://openweathermap.org/img/wn/03n@2x.png"),
    },
    45: {
        "day": ("Foggy", "http://openweathermap.org/img/wn/50d@2x.png"),
        "night": ("Foggy", "http://openweathermap.org/img/wn/50n@2x.png"),
    },
    48: {
        "day": ("Rime Fog", "http://openweathermap.org/img/wn/50d@2x.png"),
        "night": ("Rime Fog", "http://openweathermap.org/img/wn/50n@2x.png"),
    },
    51: {
        "day": ("Light Drizzle", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Light Drizzle", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    53: {
        "day": ("Drizzle", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Drizzle", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    55: {
        "day": ("Heavy Drizzle", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Heavy Drizzle", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    56: {
        "day": (
            "Light Freezing Drizzle",
            "http://openweathermap.org/img/wn/09d@2x.png",
        ),
        "night": (
            "Light Freezing Drizzle",
            "http://openweathermap.org/img/wn/09n@2x.png",
        ),
    },
    57: {
        "day": ("Freezing Drizzle", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Freezing Drizzle", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    61: {
        "day": ("Light Rain", "http://openweathermap.org/img/wn/10d@2x.png"),
        "night": ("Light Rain", "http://openweathermap.org/img/wn/10n@2x.png"),
    },
    63: {
        "day": ("Rain", "http://openweathermap.org/img/wn/10d@2x.png"),
        "night": ("Rain", "http://openweathermap.org/img/wn/10n@2x.png"),
    },
    65: {
        "day": ("Heavy Rain", "http://openweathermap.org/img/wn/10d@2x.png"),
        "night": ("Heavy Rain", "http://openweathermap.org/img/wn/10n@2x.png"),
    },
    66: {
        "day": ("Freezing Rain", "http://openweathermap.org/img/wn/10d@2x.png"),
        "night": ("Freezing Rain", "http://openweathermap.org/img/wn/10n@2x.png"),
    },
    67: {
        "day": ("Freezing Rain", "http://openweathermap.org/img/wn/10d@2x.png"),
        "night": ("Freezing Rain", "http://openweathermap.org/img/wn/10n@2x.png"),
    },
    71: {
        "day": ("Light Snow", "http://openweathermap.org/img/wn/13d@2x.png"),
        "night": ("Light Snow", "http://openweathermap.org/img/wn/13n@2x.png"),
    },
    73: {
        "day": ("Snow", "http://openweathermap.org/img/wn/13d@2x.png"),
        "night": ("Snow", "http://openweathermap.org/img/wn/13n@2x.png"),
    },
    75: {
        "day": ("Heavy Snow", "http://openweathermap.org/img/wn/13d@2x.png"),
        "night": ("Heavy Snow", "http://openweathermap.org/img/wn/13n@2x.png"),
    },
    77: {
        "day": ("Snow Grains", "http://openweathermap.org/img/wn/13d@2x.png"),
        "night": ("Snow Grains", "http://openweathermap.org/img/wn/13n@2x.png"),
    },
    80: {
        "day": ("Light Showers", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Light Showers", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    81: {
        "day": ("Showers", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Showers", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    82: {
        "day": ("Heavy Showers", "http://openweathermap.org/img/wn/09d@2x.png"),
        "night": ("Heavy Showers", "http://openweathermap.org/img/wn/09n@2x.png"),
    },
    85: {
        "day": ("Snow Showers", "http://openweathermap.org/img/wn/13d@2x.png"),
        "night": ("Snow Showers", "http://openweathermap.org/img/wn/13n@2x.png"),
    },
    86: {
        "day": ("Snow Showers", "http://openweathermap.org/img/wn/13d@2x.png"),
        "night": ("Snow Showers", "http://openweathermap.org/img/wn/13n@2x.png"),
    },
    95: {
        "day": ("Thunderstorm", "http://openweathermap.org/img/wn/11d@2x.png"),
        "night": ("Thunderstorm", "http://openweathermap.org/img/wn/11n@2x.png"),
    },
    96: {
        "day": (
            "Thunderstorm With Hail",
            "http://openweathermap.org/img/wn/11d@2x.png",
        ),
        "night": (
            "Thunderstorm With Hail",
            "http://openweathermap.org/img/wn/11n@2x.png",
        ),
    },
    99: {
        "day": (
            "Thunderstorm With Hail",
            "http://openweathermap.org/img/wn/11d@2x.png",
        ),
        "night": (
            "Thunderstorm With Hail",
            "http://openweathermap.org/img/wn/11n@2x.png",
        ),
    },
}


# Gives baufort scale value for speed in kmh
def to_baufort(windspeed):
    scale = [1, 6, 12, 20, 29, 39, 50, 62, 75, 89, 103, 118]
    i = 0
    while i < len(scale) and windspeed > scale[i]:
        i += 1
    return i


def get_human(data):
    when = "day" if data["is_day"] == 1 else "night"
    return CODES[data["weathercode"]][when]


def fetch_data(
    latitude, longitude, location, temperature_unit="celsius", windspeed_unit="kmh"
):
    # Not using match as default python in RaspberryOS is outdated
    if windspeed_unit == "mph":
        wind_scale = 1.61
    elif windspeed_unit == "ms":
        wind_scale = 3.6
    elif windspeed_unit == "kn":
        wind_scale = 1.852
    else:
        windspeed_unit = "kmh"
        wind_scale = 1

    url = (
        "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&hourly=precipitation&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,windspeed_10m_max&current_weather=true&timezone=auto&temperature_unit=%s&windspeed_unit=%s"
        % (latitude, longitude, temperature_unit, windspeed_unit)
    )
    response = requests.get(url)
    raw_data = json.loads(response.text)

    TEMPUNIT = raw_data["daily_units"]["temperature_2m_max"]
    WINDUNIT = raw_data["daily_units"]["windspeed_10m_max"]
    windspeed = raw_data["current_weather"]["windspeed"]
    description, image_url = get_human(raw_data["current_weather"])
    data = {
        "baufort": to_baufort(windspeed * wind_scale),
        "icon": raw_data["current_weather"]["weathercode"],
        "precipitation": raw_data["hourly"]["precipitation"],
        "range": str(round(raw_data["daily"]["temperature_2m_min"][0]))
        + "—"
        + str(round(raw_data["daily"]["temperature_2m_max"][0]))
        + TEMPUNIT,
        "sunrise": raw_data["daily"]["sunrise"][0],
        "sunset": raw_data["daily"]["sunset"][0],
        "temp": str(round(raw_data["current_weather"]["temperature"])) + TEMPUNIT,
        "wind": str(round(windspeed)) + WINDUNIT,
        # XS"wind_direction": raw_data["current_weather"]["wind_direction"],
        "TEMPUNIT": TEMPUNIT,
        "WINDUNIT": WINDUNIT,
        "description": description,
        "image_url": image_url,
        "location": location,
    }

    return data


def make_weather_image():
    data = fetch_data(
        latitude=37.87159,
        longitude=-122.27275,
        location="Berkeley, CA",
        temperature_unit="fahrenheit",
    )
    tmpdir = tempfile.TemporaryDirectory()
    with open(os.path.join(tmpdir.name, "index.html"), "w") as f:
        f.write(chevron.render(HTML_TEMPLATE, data))
    return render_image(tmpdir)
