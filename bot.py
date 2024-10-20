import uuid

from flask import Flask, jsonify, make_response, redirect, request, url_for
from src.bot.music_agent import MusicAgent
from src.db import add_user, get_user
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.secret_key = "super_secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    print("index")
    return redirect(url_for("chat"))


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    try:
        user = get_user(username)
        response = make_response(redirect(url_for("chat")))
        response.set_cookie("username", user.username)
        return response
    except ValueError:
        return make_response(redirect(url_for("register")))


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    try:
        user = add_user(username, email)
        response = make_response(redirect(url_for("chat")))
        response.set_cookie("username", user.username)
        return response
    except ValueError:
        return make_response(redirect(url_for("login")))


@app.route("/chat", methods=["POST"])
def chat():
    print("chat")
    user = get_user(request.cookies.get("username"))
    if not user:
        return make_response(redirect(url_for("login")))

    bot = MusicAgent(user)

    msg = request.json.get("message")
    cmd = msg.split(" ")[0]

    if "/help" in cmd:
        result = bot.help_cmd()

    elif "/exit" in cmd:
        result = bot.goodbye()

    elif "/add_song" in cmd:
        if len(msg.split(" ")) != 3:
            raise ValueError("Usage: /add_song <song_name> <playlist_name>")
        _, song_name, playlist_name = msg.split(" ")
        result = bot.add_song_cmd(song_name, playlist_name)

    elif "/remove_song" in cmd:
        if len(msg.split(" ")) != 3:
            raise ValueError("Usage: /remove_song <song_name> <playlist_name>")
        _, song_name, playlist_name = msg.split(" ")
        result = bot.remove_song_cmd(song_name, playlist_name)

    elif "/create_playlist" in cmd:
        if len(msg.split(" ")) != 2:
            raise ValueError("Usage: /create_playlist <playlist_name>")
        _, playlist_name = msg.split(" ")
        result = bot.create_playlist_cmd(playlist_name)

    elif "/delete_playlist" in cmd:
        if len(msg.split(" ")) != 2:
            raise ValueError("Usage: /delete_playlist <playlist_name>")
        _, playlist_name = msg.split(" ")
        result = bot.delete_playlist_cmd(playlist_name)

    elif "/list_playlists" in cmd:
        result = bot.list_playlists_cmd()

    elif "/list_songs" in cmd:
        if len(msg.split(" ")) != 2:
            raise ValueError("Usage: /list_songs <playlist_name>")
        _, playlist_name = msg.split(" ")
        result = bot.list_songs_cmd(playlist_name)

    elif "/lookup" in cmd:
        if len(msg.split(" ")) < 2:
            raise ValueError("Usage: /lookup <query>")
        _, arg = " ".join(msg.split(" "))
        result = bot.lookup_cmd(arg)

    else:
        result = bot.get_response(msg)

    socketio.emit("message", result)

    return jsonify({"message": result})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
