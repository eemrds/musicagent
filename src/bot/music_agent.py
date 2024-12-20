"""Music agent.

Agent that lets the user interract with a muscic database by asking questions 
about music, artists, albums, etc.

It also allows the user to create playlists and add songs to them using the chat 
agent.

"""

from random import randint
from typing import List, Optional
from dialoguekit.core.annotated_utterance import AnnotatedUtterance
from dialoguekit.core.dialogue_act import DialogueAct
from dialoguekit.core.utterance import Utterance
from dialoguekit.participant.agent import Agent
from dialoguekit.participant.participant import DialogueParticipant
from collections import Counter
import requests

from src.bot.llm import get_entities, get_position
from src.db import (
    MusicDB,
    add_user,
    get_user,
    search_artist,
    search_artist_albums,
    search_song,
    search_song_release,
    search_specific_song,
    search_song_artist,
    search_song_artist_genre,
    search_song_broad,
    search_spotify_playlist,
)

WELCOME_MESSAGE = "Hello, I'm MusicAgent. What can I help u with?"
GOODBYE_MESSAGE = "It was nice talking to you. Bye"
NOT_LOGGED_IN_MESSAGE = "You are not logged in. Please login or register by using /login or /register."
HELP_MESSAGE = """Available commands:
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
        self.user = MusicDB(get_user("erik"))
        self.recommended = []
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
            "song_release": self.song_release_cmd,
            "artist_album_count": self.artist_album_count_cmd,
            "delete_song_positional": self.delete_song_positional_cmd,
            "add_song_positional": self.add_song_positional_cmd,
            "add_artist": self.simulate_playlist_cmd,
            "add_song_simulation": self.add_song_simulation_cmd,
            # "recommend_songs": self.recommend_cmd,
        }

    def welcome(self) -> None:
        """Sends the agent's welcome message."""
        utterance = AnnotatedUtterance(
            "Hello, I'm MusicAgent. What can I help u with?",
            participant=DialogueParticipant.AGENT,
            utterance_id="welcome",
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def goodbye(self) -> None:
        """Sends the agent's goodbye message."""
        utterance = AnnotatedUtterance(
            "It was nice talking to you. Bye",
            dialogue_acts=[DialogueAct(intent=self.stop_intent)],
            participant=DialogueParticipant.AGENT,
            utterance_id="goodbye",
        )
        self._dialogue_connector.register_agent_utterance(utterance)

    def help_cmd(self) -> str:
        """Shows help message."""
        return HELP_MESSAGE

    def goodbye(self) -> str:
        """Exits the chat."""
        return GOODBYE_MESSAGE

    def add_song_simulation_cmd(self, **kwargs) -> str:
        """Adds a song to a playlist.

        Args:
            song_name: Name of the song.
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        playlist_name = kwargs.get("playlist")
        playlist = self.user.get_playlist(playlist_name)
        songs = [song.title for song in playlist.songs]

        found_songs = search_artist(song_name)
        found_songs = [
            song for song in found_songs if song["title"] not in songs
        ]
        if not found_songs:
            return f"All available songs by {song_name} are already in the playlist."

        song = found_songs[randint(0, len(found_songs) - 1)]
        self.user.add_song_to_playlist(song, playlist_name)
        return f"Added \"{song['title']}\" by \"{song['artist']}\" to {playlist_name}"

    def add_song_cmd(self, **kwargs) -> str:
        """Adds a song to a playlist.

        Args:
            song_name: Name of the song.
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        playlist_name = kwargs.get("playlist", "test")
        artist = kwargs.get("artist")
        playlist = self.user.get_playlist(playlist_name)
        song_specific = search_song(song_name, artist)

        if not song_specific:
            return f"""Song {song_name} was not found"""

        if not song_specific == None:
            if len(song_specific) > 1:
                buttons = [
                    {
                        "title": f"{s.title} by {s.artist}",
                        "payload": f"/add_song_btn {s.title} by {s.artist} to {playlist_name}",
                        "button_type": "button",
                    }
                    for s in song_specific[
                        :5
                    ]  # Create buttons for the first 5 songs
                ]
                msg = f"Multiple songs found. Please select one:"
                attachment = {
                    "type": "buttons",
                    "payload": {"buttons": buttons},
                }
                return {"text": msg, "attachments": [attachment]}
            elif len(song_specific) == 1:
                selected_song = song_specific[0]

                self.user.add_song_to_playlist(selected_song, playlist.name)
                return f"""Song {selected_song} added to {playlist_name}

        How about trying asking what albums feature this song by typing:
        Which album features song {selected_song.title}?"""

        songs_text = search_song_broad(song_name)

        if not songs_text == None:
            if len(songs_text) > 1:
                buttons = [
                    {
                        "title": f"{s.title} by {s.artist}",
                        "payload": f"/add_song_btn {s.title} by {s.artist} to {playlist_name}",
                        "button_type": "button",
                    }
                    for s in songs_text[
                        :5
                    ]  # Create buttons for the first 5 songs
                ]
                msg = f"Multiple songs found. Please select one:"
                attachment = {
                    "type": "buttons",
                    "payload": {"buttons": buttons},
                }
                return {"text": msg, "attachments": [attachment]}
            elif len(songs_text) == 1:
                selected_song = songs_text[0]

                self.user.add_song_to_playlist(selected_song, playlist.name)
                return f"""Song {selected_song} added to {playlist_name}

        How about trying asking what albums feature this song by typing:
        Which album features song {selected_song.title}?"""

        return f"""Song {selected_song} can not be found"""

    def add_song_artist_cmd(self, **kwargs) -> str:
        """Adds a song to a playlist.

        Args:
            song_name: Name of the song.
            artist: Name of artist
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        artist = kwargs.get("artist")
        playlist_name = kwargs.get("playlist")
        playlist = self.user.get_playlist(playlist_name)
        song = search_song(song_name, artist)
        selected_song = None

        if song is not None:
            if len(song) > 1:
                buttons = [
                    {
                        "title": f"{s.title} by {s.artist}",
                        "payload": f"/add_song_btn {s.title} by {s.artist} to {playlist_name}",
                        "button_type": "button",
                    }
                    for s in song[:5]  # Create buttons for the first 5 songs
                ]
                msg = f"Multiple songs found. Please select one:"
                attachment = {
                    "type": "buttons",
                    "payload": {"buttons": buttons},
                }
                return {"text": msg, "attachments": [attachment]}
            elif len(song) == 1:
                selected_song = song[0]

                self.user.add_song_to_playlist(selected_song, playlist.name)
                return f"""Song {selected_song} added to {playlist_name}

        How about trying asking how many albums the artist has released:
    How many albums has artist {artist} released?"""

        songs_text = search_song_broad(song_name, artist)

        if not songs_text == None:
            if len(songs_text) > 1:
                buttons = [
                    {
                        "title": f"{s.title} by {s.artist}",
                        "payload": f"/add_song_btn {s.title} by {s.artist} to {playlist_name}",
                        "button_type": "button",
                    }
                    for s in songs_text[
                        :5
                    ]  # Create buttons for the first 5 songs
                ]
                msg = f"Multiple songs found. Please select one:"
                attachment = {
                    "type": "buttons",
                    "payload": {"buttons": buttons},
                }
                return {"text": msg, "attachments": [attachment]}
            elif len(songs_text) == 1:
                selected_song = songs_text[0]

                self.user.add_song_to_playlist(selected_song, playlist.name)
                return f"""Song {selected_song} added to {playlist_name}

        How about trying asking what albums feature this song by typing:
        Which album features song {selected_song.title}?"""

        return f"""Song {selected_song} can not be found"""

    def add_song_artist_btn_cmd(
        self, song_name: str, artist: str, playlist_name: str
    ) -> str:
        """Adds a song to a playlist.

        Args:
            song_name: Name of the song.
            artist: Name of artist
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist = self.user.get_playlist(playlist_name)
        selected_song = search_specific_song(song_name, artist)

        if selected_song:
            self.user.add_song_to_playlist(selected_song, playlist.name)
            return f"""Song {selected_song} added to {playlist_name}

            How about trying asking how many albums the artist has released:
How many albums has artist {artist} released?"""

        return f"""Song {selected_song} not found"""

    def recommend_songs_cmd(self, **kwargs) -> dict:
        playlist_name = kwargs.get("playlist")
        loop = kwargs.get("loop", False)
        playlist = self.user.get_playlist(playlist_name)
        old_song_ids = {
            f"{song.artist}-{song.title}" for song in playlist.songs
        }

        recommendations = []

        if not loop:
            artist_counts = Counter(
                song.artist for song in playlist.songs if song.artist
            )

            # Sort by occurrence in descending order and return as a dictionary
            sorted_artist_counts = dict(
                sorted(
                    artist_counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )

            top_artists = list(sorted_artist_counts.keys())[:3]

            genre_counts = Counter(
                genre
                for song in playlist.songs
                if song.genre
                for genre in (
                    song.genre if isinstance(song.genre, list) else [song.genre]
                )
            )
            sorted_genre_counts = dict(
                sorted(
                    genre_counts.items(), key=lambda item: item[1], reverse=True
                )
            )

            top_genre = list(sorted_genre_counts.keys())[:3]

            for artist in top_artists:
                for genre in top_genre:
                    recommended_songs = search_song_artist_genre(artist, genre)
                    if not recommended_songs == None:
                        for recommended in recommended_songs:
                            song_id = (
                                f"{recommended.artist}-{recommended.title}"
                            )
                            if song_id not in old_song_ids:
                                recommendations.append(recommended)
                                old_song_ids.add(
                                    song_id
                                )  # Add unique identifier to the set
                                break

            if recommendations == []:
                return "No recommendations were found"
        else:
            # If just done button
            if self.recommended.count == 1:
                return "You have added all my recommendations. Is there anything else you want to add?"

            for recommended in self.recommended:
                song_id = f"{recommended.artist}-{recommended.title}"
                if song_id not in old_song_ids:
                    recommendations.append(recommended)

        self.recommended = recommendations

        buttons = [
            {
                "title": f"{s.title} by {s.artist}",
                "payload": f"/add_song_review {s.title} by {s.artist} to {playlist_name}",
                "button_type": "button",
            }
            for s in recommendations[:5]  # Create buttons for the first 5 songs
        ]

        # Add the "Done" button
        buttons.append(
            {"title": "Done", "payload": "Thank you!", "button_type": "button"}
        )

        msg = f"Multiple songs found. Please select one at a time. Click done when you added all the songs you want:"
        attachment = {"type": "buttons", "payload": {"buttons": buttons}}
        return {"text": msg, "attachments": [attachment]}

    def simulate_playlist_cmd(self, **kwargs) -> str:
        playlist_name = kwargs.get("playlist")
        artist_name = kwargs.get("artist")
        playlist = self.user.get_playlist(playlist_name)
        songs = [song.title for song in playlist.songs]

        found_songs = search_artist(artist_name)
        found_songs = [
            song for song in found_songs if song["title"] not in songs
        ]
        if not found_songs:
            return f"All available songs by {artist_name} are already in the playlist."

        song = found_songs[randint(0, len(found_songs) - 1)]
        self.user.add_song_to_playlist(song, playlist_name)
        return f"Added \"{song['title']}\" by \"{song['artist']}\" to {playlist_name}"

    def remove_song_cmd(self, **kwargs) -> str:
        """Removes a song from a playlist.

        Args:
            song_name: Name of the song.
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        playlist_name = kwargs.get("playlist")
        self.user.remove_song_from_playlist(song_name, playlist_name)
        return f"Song {song_name} removed from {playlist_name}"

    def list_playlists_cmd(self, **kwargs) -> str:
        """Lists all available playlists.

        Returns:
            Dict of playlists.
        """
        playlists = self.user.get_playlists()
        data = ""
        for i, playlist in enumerate(playlists):
            data += f"{i+1}. {playlist.name}\n"
        return data

    def create_playlist_cmd(self, **kwargs) -> str:
        """Creates a new playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist_name = kwargs.get("playlist")
        self.user.add_playlist(playlist_name)
        return f"Playlist {playlist_name} created"

    def playlist_desc_cmd(self, playlist_description: str) -> str:
        self.user = MusicDB(get_user(self.user.user.username))
        self.user.add_playlist(playlist_description)

        songs = search_spotify_playlist(playlist_description)

        for s in songs:
            self.user.add_song_to_playlist(s, playlist_description)

        return f"Playlist {playlist_description} created"

    def delete_playlist_cmd(self, **kwargs) -> str:
        """Deletes a playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist_name = kwargs.get("playlist")
        self.user.remove_playlist(playlist_name)
        self.user = MusicDB(get_user(self.user.user.username))
        return f"Playlist {playlist_name} deleted"

    def list_songs_cmd(self, **kwargs) -> str:
        """Lists all songs in a playlist.

        Args:
            playlist_name: Name of the playlist.

        Returns:
            Tuple containing the response.
        """
        playlist_name = kwargs.get("playlist")
        data = ""
        for i, song in enumerate(
            self.user.user.playlists.get(playlist_name).songs
        ):
            data += f"{i+1}. {song.title} by {song.artist}\n"
        return data

    def search_song_cmd(self, **kwargs) -> List[dict]:
        """Looks up a query in the music database.

        Args:
            arg: Command argument.

        Returns:
            Dict of songs.
        """
        arg = kwargs.get("song")
        data = ""
        for i, song in enumerate(search_song(arg)):
            data += f"{i+1}. {song.title} by {song.artist}\n"
        return data

    def song_release_cmd(self, **kwargs) -> str:
        """Search for release date of an album.

        Returns:
            Tuple containing the response.
        """
        song_name = kwargs.get("song")
        artist_name = kwargs.get("artist")

        results = search_song_release(song_name, artist_name)

        return f"{song_name} was released in {results}"

    def artist_album_count_cmd(self, **kwargs) -> str:
        """Search for release date of an album.

        Returns:
            Tuple containing the response.
        """
        artist = kwargs.get("artist")
        result = search_artist_albums(artist)
        return (
            f"{artist} has released {len(set(result))} albums. Some are:\n* "
            + "\n* ".join(list(set(result))[:5])
        )

    def delete_song_positional_cmd(self, **kwargs) -> str:
        """Search for release date of an album.

        Returns:
            Tuple containing the response.
        """
        playlist = kwargs.get("playlist")
        playlist = self.user.get_playlist(playlist)
        songs = [song.title for song in playlist.songs]
        position = get_position(kwargs.get("input"), songs)
        for song in position:
            self.user.remove_song_from_playlist(song, playlist.name)
        return f"{len(position)} songs removed from {playlist.name}"

    def add_song_positional_cmd(self, **kwargs) -> str:
        """Search for release date of an album.

        Returns:
            Tuple containing the response.
        """
        pass
        # album_name = kwargs.get("album")
        # return f"Album {album_name} was released on {album.release_date}"

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
            - /playlist <playlist_description>: Creates a new playlist based on description.
            - /delete_playlist <playlist_name>: Deletes a playlist.
            - /list_playlists: Lists all available playlists.
            - /recommend <playlist_name>: Recommends songs based on playlist.
            - /list_songs <playlist_name>: Lists all songs in a playlist.
            - /lookup <query>: Looks up a query in the music database.
            - /login <username>: Logs in the user.
            - /register <username> *<email>*: Registers the user.

        Args:
            utterance: User utterance.
        """
        try:
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
                    utterance_id="not_logged_in",
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

            if msg == "Thank you!":
                result = "Your welcome!"

            # bot = MusicAgent(self.user)

            if utterance.text[0] == "/":
                cmd = utterance.text.split(" ")[0]

            if "/help" in cmd:
                result = self.help_cmd()

            elif "/exit" in cmd:
                result = self.goodbye()

            elif "/add_song_btn" in cmd:
                if len(msg.split(" ")) < 4:
                    # /add_song diamonds by rihanna to playlist2
                    raise ValueError(
                        "Usage: /add_song <song_name> to <playlist_name>"
                    )
                args = msg.split(" ", 1)[1]
                songinfo, playlist_name = args.split(" to ")

                if " by " in songinfo:
                    song_name, artist = songinfo.split(" by ")
                    result = self.add_song_artist_btn_cmd(
                        song_name, artist, playlist_name
                    )

            elif "/add_song_review" in cmd:
                if len(msg.split(" ")) < 4:
                    # /add_song diamonds by rihanna to playlist2
                    raise ValueError(
                        "Usage: /add_song_btn <song_name> to <playlist_name>"
                    )
                args = msg.split(" ", 1)[1]
                songinfo, playlist_name = args.split(" to ")

                if " by " in songinfo:
                    song_name, artist = songinfo.split(" by ")
                    _ = self.add_song_artist_btn_cmd(
                        song_name, artist, playlist_name
                    )
                    result = self.recommend_songs_cmd(
                        **{"playlist": playlist_name, "loop": True}
                    )

            elif "/add_song" in cmd:
                if len(msg.split(" ")) < 4:
                    # /add_song diamonds by rihanna to playlist2
                    raise ValueError(
                        "Usage: /add_song <song_name> to <playlist_name>"
                    )
                args = msg.split(" ", 1)[1]
                songinfo, playlist_name = args.split(" to ")

                if " by " in songinfo:
                    song_name, artist = songinfo.split(" by ")
                    result = self.add_song_artist_cmd(
                        song_name, artist, playlist_name
                    )
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

            elif "/playlist" in cmd:
                if len(msg.split(" ")) < 2:
                    raise ValueError("Usage: /playlist <playlist_description>")
                playlist_description = msg.split(" ", 1)[1]
                result = self.playlist_desc_cmd(playlist_description)

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

            elif "/recommend" in cmd:
                if len(msg.split(" ")) < 2:
                    raise ValueError("Usage: /recommend <playlist_name>")

                playlist_name = msg.split(" ", 1)[1]

                result = self.recommend_songs_cmd(
                    **{"playlist": playlist_name, "loop": False}
                )

            if "/" not in msg and msg != "Thank you!":
                intent, entities = get_entities(
                    msg, self.user.user.playlists.dump()
                )
                entities["input"] = msg
                if not intent:
                    result = "Sorry, I didn't get that."
                else:
                    result = self.intents[intent](**entities)
                if not result:
                    result = "Sorry, I didn't get that."
            self.user = MusicDB(get_user(self.user.user.username))
            response = AnnotatedUtterance(
                str(result),
                participant=DialogueParticipant.AGENT,
                utterance_id="response",
            )
            if "/exit" in cmd:
                response = AnnotatedUtterance(
                    str(result),
                    participant=DialogueParticipant.AGENT,
                    utterance_id="response",
                    dialogue_acts=[DialogueAct(intent=self.stop_intent)],
                )
            self._dialogue_connector.register_agent_utterance(response)
        except Exception as e:
            self._dialogue_connector.register_agent_utterance(
                AnnotatedUtterance(
                    str("Sorry, I didn't get that."),
                    participant=DialogueParticipant.AGENT,
                    utterance_id="error",
                )
            )
