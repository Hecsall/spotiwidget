# Spotify Widget

> ### **WIP** - for now it has only the default theme from kittinan's repo, but no actual parameters to customize it, i'm  working on it.

"Currently Playing" SVG Spotify Widget.

This project used to be a fork of [https://github.com/kittinan/spotify-github-profile](https://github.com/kittinan/spotify-github-profile) but since a lot of python code changed, I decided to start a separate repo for it.

## **Things that changed**
- **Auto refresh**: I added a `<script>` tag inside the SVG that will auto refresh the widget when a song ends. *(Probably won't work on GitHub)*
- **Song progress**: With the `<script>` of the point above, it's now possible to have a progress bar to show the song progress (almost entirely in CSS). *(Probably won't work on GitHub)*
- **Upgraded dependencies**: Not a big deal, but I bumped all the dependencies versions to the latest available.
- **SCSS styles**: Theme styles in SCSS (compiled when `app.py` runs).

## **TODO**
- Plan how to manage widgets width and height automatically
- Optimize themes visuals (like scrolling titles)
- More customizations parameters
- Spotify Developer Guidelines compliancy
- "OBS-friendly" usage (as browser source)