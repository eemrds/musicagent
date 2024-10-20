"""Music agent.

Agent that lets the user interract with a muscic database through commands or
natural language.
"""

import requests

from src.bot.actions import *
from src.db import MusicDB, search_artist, search_song

RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"
WELCOME_MESSAGE = "Hello, I'm MusicAgent. What can I help u with?"
GOODBYE_MESSAGE = "It was nice talking to you. Bye"
NOT_LOGGED_IN_MESSAGE = "You are not logged in. Please login or register by using /login or /register."
HELP_MESSAGE = """
Available commands:
    - /help: Shows help message.
    - /exit: Exits the chat.
    - /add_song <song_name> <playlist_name>: Adds a song to a playlist.
    - /remove_song <song_name> <playlist_name>: Removes a song from a playlist.
    - /create_playlist <playlist_name>: Creates a new playlist.
    - /delete_playlist <playlist_name>: Deletes a playlist.
    - /list_playlists: Lists all available playlists.
    - /list_songs <playlist_name>: Lists all songs in a playlist.
    - /lookup <query>: Looks up a query in the music database.
"""


class MusicAgent:
    def __init__(self, user: MusicDB):
        """Music agent.

        Agent that lets the user interract with a muscic database through
        commands or natural language.

        Args:
            user: UserDB instance.
        """
        self.user = user

    def help_cmd(self) -> str:
        """Shows help message."""
        return HELP_MESSAGE

    def goodbye(self) -> str:
        """Exits the chat."""
        return GOODBYE_MESSAGE

    def add_song_cmd(self, song_name: str, playlist_name: str) -> str:
        """Adds a song to a playlist.

        Args:
            song_name: Name of the song.
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist = self.user.get_playlist(playlist_name)
        song = search_song(song_name)
        selected_song = None

        if len(song) > 1:
            song_str = "\n".join(
                [f"{i+1}. {s.dump()}" for i, s in enumerate(song)]
            )
            msg = f"Multiple songs found. Please select one:\n{song_str}"
            num = self.clarify_utterance(msg)
            selected_song = song[int(num) - 1]
        elif len(song) == 1:
            selected_song = song[0]
        else:
            return f"Song {song_name} not found", None

        self.user.add_song_to_playlist(selected_song, playlist.name)
        return f"Song {selected_song} added to {playlist_name}"

    def remove_song_cmd(self, song_name: str, playlist_name: str) -> str:
        """Removes a song from a playlist.

        Args:
            song_name: Name of the song.
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist = self.user.get_playlist(playlist_name)
        song = self.user.get_song_from_playlist(playlist_name, song_name)
        self.user.remove_song_from_playlist(song, playlist)
        return f"Song {song_name} removed from {playlist_name}"

    def list_playlists_cmd(self) -> dict:
        """Lists all available playlists.

        Returns:
            Dict of playlists.
        """
        playlists = self.user.get_playlists()
        return playlists.dump()

    def create_playlist_cmd(self, playlist_name: str) -> str:
        """Creates a new playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        self.user.add_playlist(playlist_name)
        return f"Playlist {playlist_name} created"

    def delete_playlist_cmd(self, playlist_name: str) -> str:
        """Deletes a playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        self.user.remove_playlist(playlist_name).dump()
        return f"Playlist {playlist_name} deleted"

    def list_songs_cmd(self, playlist_name: str) -> str:
        """Lists all songs in a playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        return self.user.playlists.get(playlist_name).songs.dump()

    def search_song_cmd(self, arg: str) -> List[dict]:
        """Looks up a query in the music database.

        Args:
            arg: Command argument.

        Returns:
            Dict of songs.
        """
        return search_song(arg).dump()

    def search_artist_cmd(self, arg: str) -> List[dict]:
        """Looks up a query in the music database.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        return search_artist(arg).dump()

    def get_response(self, msg: str) -> str:
        """Get response to a message.

        Args:
            msg: User message.

        Returns:
            Tuple containing the response.
        """
        return requests.post(RASA_SERVER_URL, json={"message": msg}).json()
