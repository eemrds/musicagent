"""Naive user simulator that simply requests a fixed list of songs."""

import json
from random import choice, randint
from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.participant import DialogueParticipant
from dialoguekit.participant.user import User, UserType

from src.bot.llm import get_entities, get_number
from src.db import MusicDB, get_user


commands = [
    "List songs in 'playlist'.",
    "Search for the number of albums by 'artist'.",
]


class NaiveUserSimulator(User):
    def __init__(
        self,
        id,
        user_type=UserType.SIMULATOR,
    ) -> None:
        """Initializes the naive user simulator.

        Args:
            id: User ID.
            user_type: User type. Defaults to UserType.SIMULATOR.
        """
        super().__init__(id, user_type)
        self._num_songs = 0
        name = id
        self.name = name
        self.user = MusicDB(get_user(name))
        self.first = False
        self.login = False
        self.stop = False
        self.create_playlist = False
        self.questions = 0
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

    def get_response(self):
        random_liked_song = choice(self.liked_songs)
        random_liked_artist = choice(self.liked_artists)
        if len(self.user.get_playlist(self.playlist_name).songs) == 0:
            self.questions += 1
            return f"Add song {random_liked_song} to {self.playlist_name} as simulation."
        else:
            if self.questions % 3 == 0 and self.questions != 0:
                self.questions += 1
                return (
                    choice(commands)
                    .replace("playlist", self.playlist_name)
                    .replace("artist", random_liked_artist)
                )
            else:
                self.questions += 1
                return f"Add artist {random_liked_artist} to playlist {self.playlist_name}."

    def get_response(self):
        if (
            len(self.user.get_playlist(self.playlist_name).songs)
            < self.num_songs
        ):
            utterance = self.get_response()
            self.user = MusicDB(get_user(self.name))
            return AnnotatedUtterance(
                utterance, participant=DialogueParticipant.USER
            )
        else:
            utterance = "/exit"
            self.user.remove_playlist(self.playlist_name)
            self.user = MusicDB(get_user(self.name))
            self.stop = True
            return AnnotatedUtterance(
                utterance,
                participant=DialogueParticipant.USER,
                # dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            )

    def _generate_response(self, utterance) -> AnnotatedUtterance:
        """Generates a response.

        Returns:
            Annotated utterance.
        """
        if not self.login:
            self.login = True
            response = AnnotatedUtterance(
                f"/login {self.name}", participant=DialogueParticipant.USER
            )
        elif self.login and not self.create_playlist:
            self.create_playlist = True
            if self.playlist_name not in self.user.get_playlists():
                response = AnnotatedUtterance(
                    f"Create a playlist called {self.playlist_name}.",
                    participant=DialogueParticipant.USER,
                )
        else:
            response = self._get_response()
        self.user = MusicDB(get_user(self.name))

        if (
            self.questions % 2 == 0
            and self.questions != 0
            and randint(0, 1) == 0
        ):
            self.questions += 1
            song_added = get_entities(utterance.text)[1]
            response = AnnotatedUtterance(
                choice(
                    [
                        "Search for release date of 'song'.".replace(
                            "song", song_added.get("song", self.liked_songs[0])
                        ),
                        "Search for the number of albums by 'artist'.".replace(
                            "artist",
                            song_added.get("artist", self.liked_artists[0]),
                        ),
                    ]
                ),
                participant=DialogueParticipant.USER,
            )
        return AnnotatedUtterance(
            response, participant=DialogueParticipant.USER
        )

    def receive_utterance(self, utterance: Utterance) -> None:
        """Gets called every time there is a new agent utterance.

        Args:
            utterance: Agent utterance.
        """
        response = self._generate_response(utterance)
        self._dialogue_connector.register_user_utterance(response)
