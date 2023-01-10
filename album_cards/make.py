import os
import tempfile

import discogs_client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from album_cards import make_card_discogs, make_card_spotify, USER_AGENT


SCOPE = "user-library-read"

d = discogs_client.Client(USER_AGENT, user_token=os.getenv("TOKEN"))
me = d.identity()
for item in me.collection_folders[0].releases:
    make_card_discogs(item.release).save(f"{item.release.id}.jpeg")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))

results = sp.current_user_saved_albums()
albums = results["items"]
while results["next"]:
    results = sp.next(results)
    albums.extend(results["items"])

for item in albums:
    make_card_spotify(item["album"]).save(f"{item['album']['id']}.jpeg")
