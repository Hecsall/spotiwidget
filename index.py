from base64 import b64decode, b64encode
from flask import Flask, session, request, render_template, redirect, Response
from flask_session import Session
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
import frozendict
from random import randint
import sass


# Compile all SCSS themes
sass.compile(
    dirname=('templates/themes', 'templates/themes')
    # output_style='compressed'
)


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
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


# Define and create cache folder if does not exists
caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


# Return session cache path for current user
def session_cache_path():
    return caches_folder + session.get('uuid')


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
    return user_id


# Homepage that handles login

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index():
    # TODO: check if this caching is necessary
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    # TODO: check if this caching is necessary
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_handler=cache_handler,
        show_dialog=True
    )

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        user_id = save_user_to_db(auth_manager=auth_manager, code=request.args.get("code"))
        return redirect('/editor?uid={}'.format(user_id))

    rendered_data = {
        "title": "Home",
    }

    # TODO: check if this caching is necessary
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        rendered_data["auth_url"] = auth_url
        rendered_data["is_authenticated"] = False
        return render_template('index.html', **rendered_data)

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    rendered_data["spotify"] = spotify
    rendered_data["is_authenticated"] = True

    return render_template('index.html', **rendered_data)


# Disconnect the user
# Remove the CACHE file (.cache-test) so that a new user can authorize.
@app.route('/sign_out')
def sign_out():
    try:
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


def get_access_token(uid):
    global CACHE_TOKEN_INFO

    token_info = CACHE_TOKEN_INFO.get(uid, None)

    # TODO: check if this caching is necessary
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_handler=cache_handler,
        show_dialog=True
    )

    if not token_info:
        # Load from firebase
        doc_ref = firebase_db.collection("users").document(uid)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        token_info = doc.to_dict()
        # Cache token_info
        CACHE_TOKEN_INFO[uid] = token_info

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
def currently_playing():
    uid = request.args.get("uid")
    if not uid:
        return redirect('/')

    # TODO: check if this caching is necessary
    if not session.get('uuid'):
        session['uuid'] = str(uuid.uuid4())

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
    song_title,
    song_artist,
    song_cover_base64,
    song_progress,
    song_duration,
    song_uri,
    is_now_playing,
    theme,
):
    if is_now_playing:
        title_text = "Now playing"
    else:
        title_text = "Recently played"

    rendered_data = {
        "title_text": title_text,
        "song_title": song_title,
        "song_artist": song_artist,
        "song_cover_base64": song_cover_base64,
        "song_progress": song_progress,
        "song_duration": song_duration,
        "song_uri": song_uri,
        "is_now_playing": is_now_playing,
        "height": '600px'
    }

    if theme != 'default':
        return render_template(f"themes/{theme}.html", **rendered_data)
    else:
        return render_template("themes/default.html", **rendered_data)


# Widget SVG direct URL
@app.route('/widget')
def widget():
    uid = request.args.get("uid")
    if not uid:
        return redirect('/')

    # TODO: check if this caching is necessary
    if not session.get('uuid'):
        session['uuid'] = str(uuid.uuid4())

    theme = request.args.get("theme", default='default')

    access_token = get_access_token(uid)
    if not access_token:
        return Response('User not authorized', status=403)

    song, is_now_playing = get_song_info(access_token)

    # Pick data we need in the widget
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
    svg_code = generate_svg(
        song_title,
        song_artist,
        song_cover_base64,
        song_progress,
        song_duration,
        song_uri,
        is_now_playing,
        theme,
    )

    resp = Response(svg_code, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    app.run(debug=True)
