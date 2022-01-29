# Spotify Widget

"Currently Playing" SVG Spotify Widget.

> This project used to be a fork of [https://github.com/kittinan/spotify-github-profile](https://github.com/kittinan/spotify-github-profile) but since a lot of python code changed, I decided to start a separate repo for it.

## **Usage**
1. Go to https://spotiwidget.vercel.app/
2. Login with your Spotify Account
3. Customize your widget as you like
4. Once done, click the **Get Widget URL** button
5. Copy the URL of the page just opened, and place that inside a Markdown image like this:
```markdown
[![SpotiWidget](generated_url)](https://github.com/Hecsall/spotiwidget)
```

## **Local development setup**
Create a Python virtualenvironment and install dependencies
> Tested with Python 3.9
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the `.env.example` file and name it `.env`, then populate it with the correct environment variables.
> `.env` file already git-ignored
- **FLASK_SECRET_KEY**: Random long string
- **SPOTIFY_CLIENT_ID**: Client ID from your spotify app (https://developer.spotify.com/dashboard/applications)
- **SPOTIFY_CLIENT_SECRET**: Client Secret from your spotify app (https://developer.spotify.com/dashboard/applications)
- **BASE_URL**: Base URL of your app, http://localhost:5000 for local development.
- **FIREBASE**: Base64 encode your Firebase credentials JSON file content and paste it here.

> Suggestion: on Spotify Developer, as "Redirect URIs" place what will be your app url (https://something.vercel.app/) along with "http://localhost:5000/", so that you will be able to login while testing locally.

Run the local development server
```sh
python index.py
```

## **Notable changes**
> :magic_wand: &rarr; Uses an internal script tag to handle dynamic changes. These scripts won't start on GitHub, but the rest of the widget will be displayed normally. 
- :magic_wand: **Auto refresh**: I added a `<script>` tag inside the SVG that will auto refresh the widget when the song ends.
- :magic_wand: **Song progress**: With the `<script>` of the point above, it's now possible to have a progress bar to show the song progress (almost entirely in CSS).
- **Upgraded dependencies**: Not a big deal, but I bumped all the dependencies versions to the latest available.
- **SCSS styles**: Theme styles in SCSS (compiled when `app.py` runs).

## **TODO**
- Plan how to manage widgets width and height automatically
- Optimize themes visuals (like scrolling titles)
- More customizations parameters
- Spotify Developer Guidelines compliancy
- "OBS-friendly" usage (as browser source)