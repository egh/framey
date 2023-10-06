# Frame

![framey example now playing](./playing.jpeg)

Framey is a system to display information on an [Inky Frame](https://shop.pimoroni.com/products/inky-frame-7-3). It consists of a client which runs on the frame and a server that runs elsewhere. The client fetches pre-dithered images from the server and displays them. The complex logic is offloaded to the server to allow more complexity in terms of what information can be fetched and more simplicity in the rendering process, by allowing the use of HTML.

Framey supports only two modules at the moment, a Spotify now playing module and a weather module.

## Installation

### Server

The server can run on any system. I’ve tested it on Ubuntu, Debian, and a raspberry pi 4 running raspian.

First, ensure you have python 3.7 and poetry install. Then run `poetry install`.

To run the server:

```
poetry run gunicorn "framey.server:app" -b 0.0.0.0:5000
```

I run this in a long running `screen` process, but you may prefer to run it on startup somehow.

### Client
Copy the files in `client` over to your Inky Frame using Thonny. Copy `CONFIG.py.example` to `CONFIG.py` You should configure the wifi and server endpoint in `CONFIG.py`.

