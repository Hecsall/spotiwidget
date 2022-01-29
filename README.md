# SpotiWidget

"Currently Playing" SVG Spotify Widget.

![SpotiWidget Example](https://raw.githubusercontent.com/Hecsall/spotiwidget/master/static/img/readme-screen.png)

> This project used to be a fork of [https://github.com/kittinan/spotify-github-profile](https://github.com/kittinan/spotify-github-profile) but since a lot code changed, I decided to start a separate repo for it.

## **Usage**
<a href="https://spotiwidget.vercel.app/" target="_blank" title="Open SpotiWidget">
    <img src="https://spotiwidget.vercel.app/static/img/open-app-button.svg">
</a>

1. Click the "Open the app" button or go to https://spotiwidget.vercel.app/
2. Login with your Spotify Account
3. Customize your widget as you like
4. Copy the generated code at the bottom of the page and place it in any Markdown file
5. Enjoy!

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
- Settings to change background, sound waves and progress bar color.
- **Upgraded dependencies**: Not a big deal, but I bumped all the dependencies versions to the latest available.
- **SCSS styles**: Theme styles in SCSS (compiled when `index.py` runs).

## **TODO**
- Plan how to manage widgets width and height automatically
- Optimize themes visuals (like scrolling titles)
- More customizations parameters
- Spotify Developer Guidelines compliancy
- "OBS-friendly" usage (as browser source)