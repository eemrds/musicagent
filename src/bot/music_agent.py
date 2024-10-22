"""Music agent.

Agent that lets the user interract with a muscic database by asking questions 
about music, artists, albums, etc.

It also allows the user to create playlists and add songs to them using the chat 
agent.

"""

from typing import List, Optional
from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
import requests

from src.db import MusicDB, add_user, get_user, search_song, search_specific_song

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


class MusicAgent(Agent):
    def __init__(self, id: str):
        """Music agent.

        Agent that lets the user interract with a muscic database through
        commands or natural language.

        Args:
            user: UserDB instance.
        """
        super().__init__(id)
        # self.user = MusicDB(get_user("erik"))
        self.user = None
        self._RASA_URI = "http://localhost:5005"

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        utterance = AnnotatedUtterance(
            "Hello, I'm MusicAgent. What can I help u with?",
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def goodbye(self) -> None:
        """Sends the agent's goodbye message."""
        utterance = AnnotatedUtterance(
            "It was nice talking to you. Bye",
            dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(utterance)

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
        song_specific = search_specific_song(song_name)

        if song_specific:
            selected_song = song_specific

            self.user.add_song_to_playlist(selected_song, playlist.name)
            return f"Song {selected_song} added to {playlist_name}"

        song = search_song(song_name)
        selected_song = None

        if len(song) > 1:
            song_str = "\n".join(
                [f"{i+1}. {s.dump()}" for i, s in enumerate(song)]
            )
            msg = f"Multiple songs found. Please select one:\n{song_str}"
            return f"{msg}"
        elif len(song) == 1:
            selected_song = song[0]
        else:
            return f"Song {song_name} not found", None

        self.user.add_songs_to_playlist(selected_song, playlist.name)
        return f"Song {selected_song} added to {playlist_name}"
    
    def add_song_artist_cmd(self, song_name: str, artist: str, playlist_name: str) -> str:
        """Adds a song to a playlist.

        Args:
            song_name: Name of the song.
            artist: Name of artist
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist = self.user.get_playlist(playlist_name)
        song = search_specific_song(song_name, artist)
        selected_song = None

        if len(song) > 1:
            song_str = "\n".join(
                [f"{i+1}. {s.dump()}" for i, s in enumerate(song)]
            )
            msg = f"Multiple songs found. Please select one:\n{song_str}"
            return f"{msg}"
        elif len(song) == 1:
            selected_song = song[0]
        else:
            return f"Song {song_name} not found", None

        self.user.add_songs_to_playlist(selected_song, playlist.name)
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

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called each time there is a new user utterance.

        If command is detected, specific command is executed. Otherwise,
        nlu model is used to get the response.

        Available commands:
            - /help: Shows help message.
            - /exit: Exits the chat.
            - /add_song <song_name> to <playlist_name>: Adds a song to a playlist.
            - /add_song <song_name> by <artist> to <playlist_name>: Adds a song by artist to a playlist.
            - /remove_song <song_name> <playlist_name>: Removes a song from a playlist.
            - /create_playlist <playlist_name>: Creates a new playlist.
            - /delete_playlist <playlist_name>: Deletes a playlist.
            - /list_playlists: Lists all available playlists.
            - /list_songs <playlist_name>: Lists all songs in a playlist.
            - /lookup <query>: Looks up a query in the music database.
            - /login <username>: Logs in the user.
            - /register <username> *<email>*: Registers the user.

        Args:
            utterance: User utterance.
        """
        msg = utterance.text
        cmd = msg.split(" ")[0]
        if (
            not self.user
            and "/login" not in utterance.text
            and "/register" not in utterance.text
        ):
            result = NOT_LOGGED_IN_MESSAGE
            response = AnnotatedUtterance(
                f"{self._id}: {result}",
                participant=DialogueParticipant.AGENT,
            )
            self._dialogue_connector.register_agent_utterance(response)
            return

        if "/login" in cmd:
            if len(msg.split(" ")) != 2:
                raise ValueError("Usage: /login <username>")
            username = msg.split(" ")[1]
            self.user = MusicDB(get_user(username))
            result = f"Logged in as {username}"

        if "/register" in cmd:
            username = msg.split(" ")[1]
            email = msg.split(" ")[2] if len(msg.split(" ")) == 3 else None
            self.user = MusicDB(add_user(username, email))
            result = f"Registered as {username}"

        # bot = MusicAgent(self.user)

        if utterance.text[0] == "/":
            cmd = utterance.text.split(" ")[0]

        if "/help" in cmd:
            result = self.help_cmd()

        elif "/exit" in cmd:
            result = self.goodbye()

        elif "/add_song" in cmd:
            if len(msg.split(" ")) < 4:
                # /add_song diamonds by rihanna to playlist2
                raise ValueError("Usage: /add_song <song_name> to <playlist_name>")
            args = msg.split(" ", 1)[1]
            songinfo, playlist_name = args.split(" to ")

            if " by " in songinfo:
                song_name, artist = songinfo.split(" by ")
                result = self.add_song_artist_cmd(song_name, artist, playlist_name)
            else:
                result = self.add_song_cmd(songinfo, playlist_name)

        elif "/remove_song" in cmd:
            if len(msg.split(" ")) != 3:
                raise ValueError(
                    "Usage: /remove_song <song_name> <playlist_name>"
                )
            _, song_name, playlist_name = msg.split(" ")
            result = self.remove_song_cmd(song_name, playlist_name)

        elif "/create_playlist" in cmd:
            if len(msg.split(" ")) < 2:
                raise ValueError("Usage: /create_playlist <playlist_name>")
            playlist_name = msg.split(" ", 1)[1]
            result = self.create_playlist_cmd(playlist_name)

        elif "/delete_playlist" in cmd:
            if len(msg.split(" ")) < 2:
                raise ValueError("Usage: /delete_playlist <playlist_name>")
            playlist_name = msg.split(" ", 1)[1]
            result = self.delete_playlist_cmd(playlist_name)

        elif "/list_playlists" in cmd:
            result = self.list_playlists_cmd()

        elif "/list_songs" in cmd:
            if len(msg.split(" ")) < 2:
                raise ValueError("Usage: /list_songs <playlist_name>")
            playlist_name = msg.split(" ", 1)[1]
            result = self.list_songs_cmd(playlist_name)

        elif "/lookup" in cmd:
            if len(msg.split(" ")) < 2:
                raise ValueError("Usage: /lookup <query>")
            _, arg = " ".join(msg.split(" "))
            result = self.search_song_cmd(arg)

        if "/" not in msg:
            requests.post(
                f"{self._RASA_URI}/conversations/{self.user.user.username}/tracker/events",
                json={
                    "event": "slot",
                    "name": "username",
                    "value": self.user.user.username,
                },
            )
            result = requests.post(
                f"{self._RASA_URI}/webhooks/rest/webhook",
                json={
                    "sender": self.user.user.username,
                    "message": f"({self.user.user.username}) " + utterance.text,
                },
            )
            result = result.json()
            if not isinstance(result, list) or not result:
                result = "Sorry, I didn't get that."
            else:
                prettyfy = ""
                if len(result) > 1:
                    prettyfy = "\n\t".join([r["text"] for r in result[1:]])
                result = f"{result[0]['text']}\n\t{prettyfy}"
            self.user = MusicDB(get_user(self.user.user.username))

        response = AnnotatedUtterance(
            str(result),
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(response)
