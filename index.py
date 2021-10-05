from base64 import b64decode, b64encode
from flask import Flask, session, request, render_template, redirect, Response
from firebase_admin import credentials, firestore
import firebase_admin
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv, find_dotenv
from time import time
import os
import json
import uuid
import functools
import requests
from random import randint
import sass


# Compile all SCSS themes
try:
    sass.compile(
        dirname=('templates/themes', 'templates/themes'),
        output_style='compressed'
    )
except Exception as e:
    print("Could not compile SCSS files")


# Load environment variables
load_dotenv(find_dotenv())


# Global Variables
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_SCOPES = ["user-read-recently-played", "user-read-currently-playing"]
BASE_URL = os.getenv("BASE_URL")
REDIRECT_URI = "{}/".format(BASE_URL)
FIREBASE_CONFIG = os.getenv("FIREBASE")
CACHE_TOKEN_INFO = {}


# Initialize Firebase
firebase_json = json.loads(b64decode(FIREBASE_CONFIG))
firebase_credentials = credentials.Certificate(firebase_json)
firebase_admin.initialize_app(firebase_credentials)
firebase_db = firestore.client()


# Initialize Flask app
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# Spotipy custom Cache Handler
# It just saves the token_info in an unused variable since
# not saving it would trigger a Spotipy error
class UselessCacheHandler(spotipy.cache_handler.CacheHandler):
    def get_cached_token(self):
        """
        Get and return a token_info dictionary object.
        """
        return session.get("unused_token_info")

    def save_token_to_cache(self, token_info):
        """
        Save a token_info dictionary object to the cache and return None.
        """
        session["unused_token_info"] = token_info
        return None


# Spotipy Auth Manager
cache_handler = UselessCacheHandler()
auth_manager = spotipy.oauth2.SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SPOTIFY_SCOPES,
    cache_handler=cache_handler,
    show_dialog=False
)


# When logging in, save the user inside the Firestore Database
def save_user_to_db(auth_manager, code):
    # Get Access Token
    token_info = auth_manager.get_access_token(request.args.get("code"), as_dict=True)
    access_token = token_info["access_token"]
    # Get User Info
    spotify_api = spotipy.Spotify(auth=access_token)
    user_id = spotify_api.me()["id"]
    # Save to Database
    doc_ref = firebase_db.collection("users").document(user_id)
    doc_ref.set(token_info)
    # Save to session
    session["token_info"] = token_info
    session["token_info"]["uid"] = user_id
    return user_id


# Homepage that handles login

@app.route('/')
def index():
    if request.args.get("code"):
        user_id = save_user_to_db(auth_manager=auth_manager, code=request.args.get("code"))
        return redirect('/editor?uid={}'.format(user_id))

    rendered_data = {"title": "Home"}

    session_token_info = session.get("token_info")
    if not auth_manager.validate_token(session_token_info):
        auth_url = auth_manager.get_authorize_url()
        rendered_data["auth_url"] = auth_url
        rendered_data["is_authenticated"] = False
    else:
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        rendered_data["spotify"] = spotify
        rendered_data["is_authenticated"] = True

    return render_template('index.html', **rendered_data)


# Disconnect the user
@app.route('/sign-out')
def sign_out():
    try:
        session.pop("token_info")
    except OSError as e:
        print("Error: %s" % (e))
    return redirect('/')


# Retrieve Access Token from Session or Firestore
def get_access_token(uid):
    token_info = session.get("token_info")

    # If getting the widget for another user, clear
    # your own token_info stored in the session
    if token_info is not None and token_info["uid"] != uid:
        token_info = None

    if token_info is None:
        doc_ref = firebase_db.collection("users").document(uid)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        token_info = doc.to_dict()

    if auth_manager.is_token_expired(token_info):
        updated_token_info = auth_manager.validate_token(token_info)
        doc_ref = firebase_db.collection("users").document(uid)
        doc_ref.update(updated_token_info)
        access_token = updated_token_info["access_token"]
    else:
        access_token = token_info["access_token"]

    return access_token


# Given a user ID, return the currently playing track
def get_song_info(access_token):
    spotify = spotipy.Spotify(auth=access_token)
    track = spotify.current_user_playing_track()
    if track is not None:
        return track, True
    else:
        # Get a random recently played track from the last 10
        tracks = spotify.current_user_recently_played(limit=10)
        track = {}
        track["item"] = tracks["items"][randint(0, 9)]["track"]
        return track, False

    return 'not playing', False


# Widget Editor page
@app.route('/editor')
def editor():
    uid = request.args.get("uid")
    if not uid:
        return redirect('/')

    access_token = get_access_token(uid)
    if not access_token:
        return Response('User not authorized', status=403)

    song, is_now_playing = get_song_info(access_token)

    rendered_data = {
        "title": "Editor",
        "uid": uid,
        "song": song,
        "is_now_playing": is_now_playing,
    }
    return render_template("editor.html", **rendered_data)


# Convert song cover to base64 to be used in the SVG
@functools.lru_cache(maxsize=128)
def load_image_b64(url):
    response = requests.get(url)
    return b64encode(response.content).decode("ascii")


# Render the Widget SVG
@functools.lru_cache(maxsize=128)
def generate_svg(
    theme,
    song_title,
    song_artist,
    song_cover_base64,
    song_progress,
    song_duration,
    song_uri,
    is_now_playing,
):
    rendered_data = {
        "song_title": song_title,
        "song_artist": song_artist,
        "song_cover_base64": song_cover_base64,
        "song_progress": song_progress,
        "song_duration": song_duration,
        "song_uri": song_uri,
        "is_now_playing": is_now_playing,
        "height": '600px'
    }

    return render_template(f"themes/{theme}.html", **rendered_data)


# Widget SVG direct URL
@app.route('/widget')
def widget():
    uid = request.args.get("uid")
    if not uid:
        return redirect('/')

    theme = request.args.get("theme", default='default')

    # Get the song info
    access_token = get_access_token(uid)
    if not access_token:
        return Response('User not authorized', status=403)
    song, is_now_playing = get_song_info(access_token)

    # Pick data we need for the widget
    song_title = song["item"]["name"]
    if song["item"]["type"] == "track":
        song_cover_base64 = load_image_b64(song["item"]["album"]["images"][0]["url"])
    elif song["item"]["type"] == "episode":
        song_cover_base64 = load_image_b64(song["item"]["images"][0]["url"])
    song_artist = song["item"]["artists"][0]["name"]
    song_progress = song["progress_ms"] if is_now_playing else 0
    song_duration = song["item"]["duration_ms"]
    song_uri = song["item"]["uri"]

    # Generate the SVG
    # I need to pass single parameters because the caching decorator
    # does not accept dictionaries/lists
    svg_code = generate_svg(
        theme,
        song_title,
        song_artist,
        song_cover_base64,
        song_progress,
        song_duration,
        song_uri,
        is_now_playing,
    )

    resp = Response(svg_code, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    app.run(debug=True)
