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

from src.bot.llm import get_entities
from src.db import MusicDB, add_user, get_user, search_song

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
    def __init__(self, id: str, use_rasa: bool = False) -> None:
        """Music agent.

        Agent that lets the user interract with a muscic database through
        commands or natural language.

        Args:
            user: UserDB instance.
        """
        super().__init__(id)
        self.user = MusicDB(get_user("erik"))
        self._RASA_URI = "http://localhost:5005"
        self.intents = {
            "list_playlists": self.list_playlists_cmd,
            "create_playlist": self.create_playlist_cmd,
            "delete_playlist": self.delete_playlist_cmd,
            "list_playlist": self.list_songs_cmd,
            "add_song": self.add_song_cmd,
            "delete_song": self.remove_song_cmd,
            "list_songs": self.list_songs_cmd,
            "search_song": self.search_song_cmd,
            "recommend_songs": self.recommend_cmd,
        }

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

    def add_song_cmd(self, **kwargs) -> str:
        """Adds a song to a playlist.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        playlist_name = kwargs.get("playlist")
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

    def remove_song_cmd(self, **kwargs) -> str:
        """Removes a song from a playlist.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        playlist_name = kwargs.get("playlist")
        playlist = self.user.get_playlist(playlist_name)
        song = self.user.get_song_from_playlist(playlist_name, song_name)
        self.user.remove_song_from_playlist(song, playlist)
        return f"Song {song_name} removed from {playlist_name}"

    def list_playlists_cmd(self, **kwargs) -> dict:
        """Lists all available playlists.

        Returns:
            Dict of playlists.
        """
        playlists = self.user.get_playlists()
        return playlists.dump()

    def create_playlist_cmd(self, **kwargs) -> str:
        """Creates a new playlist.

        Returns:
            Tuple containing the response.
        """
        playlist_name = kwargs.get("playlist")
        self.user.add_playlist(playlist_name)
        return f"Playlist {playlist_name} created"

    def delete_playlist_cmd(self, **kwargs) -> str:
        """Deletes a playlist.

        Returns:
            Tuple containing the response.
        """
        playlist_name = kwargs.get("playlist")
        self.user.remove_playlist(playlist_name).dump()
        return f"Playlist {playlist_name} deleted"

    def list_songs_cmd(self, **kwargs) -> str:
        """Lists all songs in a playlist.

        Returns:
            Tuple containing the response.
        """
        return self.user.user.playlists.get(kwargs.get("playlist")).songs.dump()

    def search_song_cmd(self, **kwargs) -> List[dict]:
        """Looks up a query in the music database.

        Args:
            arg: Command argument.

        Returns:
            Dict of songs.
        """
        if kwargs.get("artist", None):
            return search_song(kwargs.get("song"), kwargs["artist"]).dump()
        return search_song(kwargs.get("song")).dump()

    def set_user(self, msg: str, cmd: str) -> str:
        """Sets the user.

        Args:
            cmd: Command.
            msg: User message.

        Returns:
            The response.
        """

        pass

    def recommend_cmd(self, playlist_name: str) -> str:
        """Recommends songs based on songs in a playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        pass

    def commands(self, msg: str) -> str:
        """Executes commands from the user.

        Args:
            msg: User message.

        Returns:
            Tuple containing the response.
        """
        cmd = msg.split(" ")[0]
        if "/help" in cmd:
            return self.help_cmd()
        elif "/exit" in cmd:
            return self.goodbye()

        elif "/login" in cmd:
            if len(msg.split(" ")) != 2:
                raise ValueError("Usage: /login <username>")
            username = msg.split(" ")[1]
            self.user = MusicDB(get_user(username))
            result = f"Logged in as {username}"

        elif "/register" in cmd:
            username = msg.split(" ")[1]
            email = msg.split(" ")[2] if len(msg.split(" ")) == 3 else None
            self.user = MusicDB(add_user(username, email))
            result = f"Registered as {username}"
        elif "/add_song" in cmd:
            if len(msg.split(" ")) != 3:
                raise ValueError("Usage: /add_song <song_name> <playlist_name>")
            _, song_name, playlist_name = msg.split(" ")
            return self.add_song_cmd(song_name, playlist_name)
        elif "/remove_song" in cmd:
            if len(msg.split(" ")) != 3:
                raise ValueError(
                    "Usage: /remove_song <song_name> <playlist_name>"
                )
            _, song_name, playlist_name = msg.split(" ")
            return self.remove_song_cmd(song_name, playlist_name)
        elif "/create_playlist" in cmd:
            if len(msg.split(" ")) != 2:
                raise ValueError("Usage: /create_playlist <playlist_name>")
            _, playlist_name = msg.split(" ")
            return self.create_playlist_cmd(playlist_name)
        elif "/delete_playlist" in cmd:
            if len(msg.split(" ")) != 2:
                raise ValueError("Usage: /delete_playlist <playlist_name>")
            _, playlist_name = msg.split(" ")
            return self.delete_playlist_cmd(playlist_name)
        elif "/list_playlists" in cmd:
            return self.list_playlists_cmd()
        elif "/list_songs" in cmd:
            if len(msg.split(" ")) != 2:
                raise ValueError("Usage: /list_songs <playlist_name>")
            _, playlist_name = msg.split(" ")
            return self.list_songs_cmd(playlist_name)
        elif "/lookup" in cmd:
            if len(msg.split(" ")) < 2:
                raise ValueError("Usage: /lookup <query>")
            _, arg = " ".join(msg.split(" "))
            return self.search_song_cmd(arg)
        else:
            return "Sorry, I didn't get that."

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called each time there is a new user utterance.

        If command is detected, specific command is executed. Otherwise,
        nlu model is used to get the response.

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

        if "/login" in msg or "/register" in msg:
            result = self.set_user(msg, cmd)

        if "/" in msg:
            result = self.commands(msg)
        else:
            intent, entities = get_entities(
                msg, self.user.user.playlists.dump()
            )
            if not intent:
                result = "Sorry, I didn't get that."
            else:
                result = self.intents[intent](**entities)
            if not isinstance(result, list) or not result:
                result = "Sorry, I didn't get that."
            else:
                prettyfy = ""
                if len(result) > 1:
                    prettyfy = "\n\t".join([str(r) for r in result[:10]])
                result = f"{result[0]}\n\t{prettyfy}"
            self.user = MusicDB(get_user(self.user.user.username))

        response = AnnotatedUtterance(
            str(result),
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(response)
