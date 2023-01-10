import os
import tempfile

import discogs_client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from album_cards import make_card, USER_AGENT


SCOPE = "user-library-read"

d = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))
me = d.identity()
for item in me.collection_folders[0].releases:
    release = item.release
    image = make_card(
        cover_url=release.images[0]["uri"],
        artist=release.artists_sort,
        album=release.title,
        year=release.year,
        qr_url=release.url,
    )
    image.save(f"{release.id}.jpeg")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))

results = sp.current_user_saved_albums()
albums = results["items"]
while results["next"]:
    results = sp.next(results)
    albums.extend(results["items"])

for item in albums:
    album = item["album"]
    image = make_card(
        cover_url=item["album"]["images"][0]["url"],
        artist=", ".join([artist["name"] for artist in album["artists"]]),
        album=album["name"],
        year=album["release_date"][0:4],
        qr_url=album["external_urls"]["spotify"],
    )
    image.save(f"{album['id']}.jpeg")
