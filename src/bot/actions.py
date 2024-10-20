from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from src.db import search_song


####################
### Song Actions ###
####################
class ActionSearchSong(Action):
    def name(self) -> Text:
        return "action_lookup_song"

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
        dispatcher.utter_elements({s.name: s.dump() for s in songs})
        return songs


class ActionAddSong(Action):
    pass


class ActionRemoveSong(Action):
    pass


########################
### Playlist Actions ###
########################
class ActionGetAllPlaylists(Action):
    pass


class ActionGetPlaylist(Action):
    pass


class ActionCreatePlaylist(Action):
    pass


class ActionDeletePlaylist(Action):
    pass
