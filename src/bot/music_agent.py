"""Music agent.

Agent that lets the user interract with a muscic database by asking questions 
about music, artists, albums, etc.

It also allows the user to create playlists and add songs to them using the chat 
agent.

"""

from typing import Optional
from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant

from src.db import UserDB, song_lookup

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

        Agent that lets the user interract with a muscic database by asking
        questions about music, artists, albums, etc. It also allows the user to
        create playlists and add songs to them using the chat agent.

        Args:
            id: Agent id.
        """
        super().__init__(id)
        self.user = UserDB("erik")
        # self.nlu = NLU()

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        utterance = AnnotatedUtterance(
            WELCOME_MESSAGE, participant=DialogueParticipant.AGENT
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def help_cmd(self) -> str:
        """Shows help message."""
        return HELP_MESSAGE

    def goodbye(self) -> str:
        """Exits the chat."""
        return GOODBYE_MESSAGE

    def clarify_utterance(self, msg: str) -> str:
        """Clarifies the user's utterance.

        Args:
            msg: User utterance.

        Returns:
            Clarified utterance.
        """
        response = AnnotatedUtterance(
            f"{self._id}: {msg}",
            participant=DialogueParticipant.AGENT,
        )
        self._dialogue_connector.register_agent_utterance(response)
        return input(f"{msg}\n")

    def add_song_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Adds a song to a playlist.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        song_name, playlist_name = arg.split(" ")
        playlist = self.user.get_playlist(playlist_name)
        song = song_lookup(song_name)
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
        return f"Song {selected_song} added to {playlist_name}", None

    def remove_song_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Removes a song from a playlist.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        song_name, playlist_name = arg.split(" ")
        playlist = self.user.get_playlist(playlist_name)
        song = song_lookup(song_name)
        self.user.remove_song_from_playlist(song, playlist)
        return f"Song {song_name} removed from {playlist_name}", None

    def list_playlists_cmd(self) -> tuple[str, Optional[str]]:
        """Lists all available playlists.

        Returns:
            Tuple containing the response.
        """
        playlists = self.user.get_playlists()
        return playlists.dump(), None

    def create_playlist_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Creates a new playlist.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        self.user.add_playlist(arg)
        return f"Playlist {arg} created", None

    def delete_playlist_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Deletes a playlist.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        self.user.remove_playlist(arg).dump()
        return f"Playlist {arg} deleted", None

    def list_songs_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Lists all songs in a playlist.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        return self.user.playlists.get(arg).songs.dump(), None

    def lookup_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Looks up a query in the music database.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        songs = song_lookup(arg)
        if len(songs) == 1:
            return songs.dump(), None

        return f"Found {len(songs)} songs.\n{songs.dump()}", None

    def login_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Logs in the user.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        user = UserDB(arg)
        self.user = user
        return f"Logged in as {arg}", None

    def register_cmd(self, arg: str) -> tuple[str, Optional[str]]:
        """Registers the user.

        Args:
            arg: Command argument.

        Returns:
            Tuple containing the response.
        """
        data = arg.split(" ")
        if len(data) == 1:
            username = data[0]
            email = None
        else:
            username = data[0]
            email = data[1]

        user = UserDB(username, email).add_user()
        self.user = user
        return f"Registered as {username}", None

    # def get_response(self, text: str) -> tuple[str, Optional[str]]:
    #     """Gets response from the NLU model.

    #     Args:
    #         text: User utterance.

    #     Returns:
    #         Tuple containing the response.
    #     """
    #     nlu =

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
        cmd = None
        extra = None
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

        if utterance.text[0] == "/":
            cmd = utterance.text.split(" ")[0]
            arg = " ".join(utterance.text.split(" ")[1:])

        if cmd == "/help":
            result = self.help_cmd()
        elif cmd == "/exit":
            result = self.goodbye()
        elif cmd == "/add_song":
            result, extra = self.add_song_cmd(arg)
        elif cmd == "/remove_song":
            result, extra = self.remove_song_cmd(arg)
        elif cmd == "/create_playlist":
            result, extra = self.create_playlist_cmd(arg)
        elif cmd == "/delete_playlist":
            result, extra = self.delete_playlist_cmd(arg)
        elif cmd == "/list_playlists":
            result, extra = self.list_playlists_cmd()
        elif cmd == "/list_songs":
            result, extra = self.list_songs_cmd(arg)
        elif cmd == "/lookup":
            result, extra = self.lookup_cmd(arg)
        elif cmd == "/login":
            result, extra = self.login_cmd(arg)
        elif cmd == "/register":
            result, extra = self.register_cmd(arg)
        else:
            # NLU model
            result, extra = self.get_response(utterance.text)

        if extra:
            result = f"{result}\n{extra}"
        response = AnnotatedUtterance(
            f"{self._id}: {result}",
            participant=DialogueParticipant.AGENT,
        )
        self.user.store_conv({"query": utterance.text, "response": result})
        self._dialogue_connector.register_agent_utterance(response)
