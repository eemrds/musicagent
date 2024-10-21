from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from src.db import MusicDB, User, get_user, search_song


def lookup_user(tracker: Tracker) -> MusicDB:
    username = tracker.get_slot("username").split(")")[0][1:]
    return MusicDB(get_user(username))


####################
### Song Actions ###
####################
# class ActionSearchSong(Action):
#     def name(self) -> Text:
#         return "action_lookup_song"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:

#         song_name = tracker.get_slot("song")
#         artist = tracker.get_slot("artist")
#         dispatcher.utter_message(text=f"Looking up song {song_name}...")

#         songs = search_song(song_name, artist)
#         dispatcher.utter_message(text=f"Found {len(songs)} song(s).")
#         dispatcher.utter_elements({s.name: s.dump() for s in songs})
#         return songs


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
        song_name = tracker.get_slot("song")
        artist = tracker.get_slot("artist")
        song = search_song(song_name, artist)
        user.add_song_to_playlist(song, playlist_name)
        dispatcher.utter_message(f"Added {song_name} to {playlist_name}.")
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
