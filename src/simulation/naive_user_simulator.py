"""Naive user simulator that simply requests a fixed list of songs."""

import json
from random import randint
from time import sleep
from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.participant import DialogueParticipant
from dialoguekit.participant.user import User, UserType

from src.bot.llm import get_entities, get_number
from src.db import MusicDB, add_user, get_user

commands = [
    "List all playlists.",
    "List the playlist 'playlist'.",
    "List songs in 'playlist'.",
    "Search for release date of 'song'.",
    "Search for the number of albums by 'artist'.",
]


class NaiveUserSimulator(User):
    def __init__(self, id, user_type=UserType.SIMULATOR) -> None:
        """Initializes the naive user simulator.

        Args:
            id: User ID.
            user_type: User type. Defaults to UserType.SIMULATOR.
            name: User name. Defaults to "steve".
        """
        super().__init__(id, user_type)
        name = id
        self.name = name
        self.user = MusicDB(get_user(name))
        self.first = False
        self.login = False
        self.create_playlist = False
        with open("src/simulation/simulation_config.json", "r") as f:
            self.preferences = json.load(f)[name]
        self.goal = self.preferences["goal"]
        self.num_songs = get_number(self.goal)
        _, self.entities = get_entities(self.goal)
        self.playlist_name = self.entities.get("playlist", "demo_playlist")
        self.liked_songs = self.preferences["liked_songs"]
        self.disliked_songs = self.preferences["disliked_songs"]
        self.liked_artists = self.preferences["liked_artists"]
        self.disliked_artists = self.preferences["disliked_artists"]

    def reject_song(self, song):
        if (
            song.title in self.disliked_song
            or song.artist in self.disliked_artists
        ):
            return f"Delete {song.title} from {self.playlist_name}."

    def generate_first_response(self):
        return self.goal

    def _generate_response(self) -> AnnotatedUtterance:
        """Generates a response.

        Returns:
            Annotated utterance.
        """
        if (
            len(self.user.get_playlist(self.playlist_name).songs)
            < self.num_songs
        ):
            utterance = self.goal
            self.user = MusicDB(get_user(self.name))
            return AnnotatedUtterance(
                utterance, participant=DialogueParticipant.USER
            )
        else:
            utterance = "/exit"
            return AnnotatedUtterance(
                utterance,
                participant=DialogueParticipant.USER,
                # dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            )

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called every time there is a new agent utterance.

        Args:
            utterance: Agent utterance.
        """
        if not self.login:
            self.login = True
            self.dialogue_connector.register_user_utterance(
                AnnotatedUtterance(
                    f"/login {self.name}", participant=DialogueParticipant.USER
                )
            )
        elif not self.create_playlist:
            self.create_playlist = True
            if self.playlist_name not in self.user.get_playlists():
                self._dialogue_connector.register_user_utterance(
                    AnnotatedUtterance(
                        f"Create a playlist called {self.playlist_name}.",
                        participant=DialogueParticipant.USER,
                    )
                )
        # elif not self.first:
        #     self.first = True
        #     first_response = self._generate_first_response()
        #     self._dialogue_connector.register_user_utterance(first_response)
        self.user = MusicDB(get_user(self.name))
        response = self._generate_response()
        self._dialogue_connector.register_user_utterance(response)
