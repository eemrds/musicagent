from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from src.bot.music_agent import HELP_MESSAGE
from src.db import (
    MusicDB,
    Song,
    get_user,
    search_artist_albums,
    search_song,
    search_album_release,
)


def lookup_user(tracker: Tracker) -> MusicDB:
    username = tracker.get_slot("username").split(")")[0][1:]
    return MusicDB(get_user(username))


####################
### Song Actions ###
####################
class ActionHelp(Action):

    def name(self) -> Text:
        return "action_help"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(HELP_MESSAGE)
        return []


class ActionSearchSong(Action):

    def name(self) -> Text:
        return "action_search_song"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        song_name = tracker.get_slot("song")
        artist = tracker.get_slot("artist")
        dispatcher.utter_message(text=f"Looking up song {song_name}...")

        songs = search_song(song_name, artist)
        dispatcher.utter_message(text=f"Found {len(songs)} song(s).")
        for i, song in enumerate(songs):
            dispatcher.utter_message(
                f"{i+1}: {song.title} - {song.artist} - {song.album} ({song.year})"
            )

        SlotSet("song_choises", songs.dump())
        return []


class ActionAskAlbumRelease(Action):

    def name(self) -> Text:
        return "action_ask_album_release"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        album_name = tracker.get_slot("album")
        result = search_album_release(album_name)
        dispatcher.utter_message(
            f"Album {album_name} was released in {result}."
        )
        return [SlotSet("album", None)]


class ActionAskArtistAlbumCount(Action):

    def name(self) -> Text:
        return "action_ask_artist_album_count"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        artist = tracker.get_slot("artist")
        albums = search_artist_albums(artist)
        dispatcher.utter_message(f"Artist {artist} has {len(albums)} albums.")

        return []


class ActionAskAlbumFromSong(Action):

    def name(self) -> Text:
        return "action_ask_album_from_song"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        song_name = tracker.get_slot("song")
        song = search_song(song_name, None)
        dispatcher.utter_message(
            f"Song {song_name} is from album {song.album}."
        )

        return []


########################
### Playlist Actions ###
########################
class ActionGetPlaylists(Action):

    def name(self) -> Text:
        return "action_get_playlists"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user = lookup_user(tracker)
        playlists = user.get_playlists()
        dispatcher.utter_message(f"Found {len(playlists)} playlist(s).")
        for playlist in playlists:
            dispatcher.utter_message(f"Playlist: {playlist.name}")
        return []


class ActionGetPlaylist(Action):

    def name(self) -> Text:
        return "action_get_playlist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user = lookup_user(tracker)
        playlist_name = tracker.get_slot("playlist")
        playlist = user.get_playlist(playlist_name)
        dispatcher.utter_message(f"Playlist: {playlist.name}")
        for song in playlist.songs:
            dispatcher.utter_message(f"Song: {song.title}")
        return []


class ActionCreatePlaylist(Action):

    def name(self) -> Text:
        return "action_create_playlist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user = lookup_user(tracker)
        playlist_name = tracker.get_slot("playlist")
        if playlist_name in user.playlists:
            dispatcher.utter_message(
                f"Playlist {playlist_name} already exists."
            )
            return []
        if not playlist_name:
            dispatcher.utter_message(
                "Please provide a different playlist name."
            )
            return []
        user.add_playlist(playlist_name)
        dispatcher.utter_message(f"Created playlist {playlist_name}.")
        return []


class ActionDeletePlaylist(Action):

    def name(self) -> Text:
        return "action_delete_playlist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user = lookup_user(tracker)
        playlist_name = tracker.get_slot("playlist")
        user.remove_playlist(playlist_name)
        dispatcher.utter_message(f"Deleted playlist {playlist_name}.")
        return []


class ActionAddSong(Action):
    def name(self) -> Text:
        return "action_add_to_playlist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user = lookup_user(tracker)
        playlist_name = tracker.get_slot("playlist")
        songs = tracker.get_slot("song_choices")
        choise = int(tracker.latest_message["text"]) - 1
        if 0 > choise >= len(songs):
            dispatcher.utter_message("Invalid song choise.")
            return []
        song = Song(**songs[choise])
        user.add_song_to_playlist(song, playlist_name)
        dispatcher.utter_message(f"Added {song.title} to {playlist_name}.")
        return []


class ActionRemoveSong(Action):
    def name(self) -> Text:
        return "action_remove_from_playlist"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user = lookup_user(tracker)
        playlist_name = tracker.get_slot("playlist")
        song_name = tracker.get_slot("song")
        user.remove_song_from_playlist(song_name, playlist_name)
        dispatcher.utter_message(f"Removed {song_name} from {playlist_name}.")
        return []
