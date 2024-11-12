import os
import re
from ollama import Client
from dotenv import load_dotenv
from ast import literal_eval

load_dotenv()

model = os.environ.get("OLLAMA_MODEL", "mistral")
ollama = Client(os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
try:
    ollama.ps()
except Exception as e:
    ollama = Client()

get_intent_prompt = """
You are MusicAgent. Your task is to extract the intent from the following input from a user: {inp}.

The possible intents are:
* help: Get help.
* list_playlists: List all playlists.
* create_playlist: Create a playlist.
* delete_playlist: Delete a playlist.
* list_playlist: List a playlist.
* add_song: Add a song to a playlist.
* delete_song: Delete a song from a playlist.
* list_songs: List songs from a playlist.
* search_song: Search for a song in a database.
* recommend_songs: Recommend songs based on songs in a playlist.

Type the intent in the following format: (intent)
DO NOT include any other text.

Examples:
* help (help)
* List all playlists. (list_playlists)
* Create a playlist named favorites. (create_playlist)
* Delete the playlist rock. (delete_playlist)
* List the playlist rock. (list_playlist)
* Add Bohemian Rhapsody to rock. (add_song)
* Delete Bohemian Rhapsody from rock. (delete_song)
* List songs in rock. (list_songs)
* Search for Bohemian Rhapsody. (search_song)
* Recommend songs for rock. (recommend_songs)
"""

get_entities_prompt = """
You are MusicAgent. Your task is to extract the entities from the following input from a user: {inp}.
The possible entities are:
* playlist: The playlist name.
* song: The song name.
* artist: The artist name.

Return the entities in a dictionary format. DO NOT include any other text.
Type the entities in the following format: {{"playlist": "playlist", "song": "song", "artist": "artist"}}
If there is no entity for a field, leave it as an empty string.

Just type the entities in a dictionary format. DO NOT include any other text.
If there is no entity for a field, leave it as an empty string.

Examples:
* Help me. {{"playlist": "", "song": "", "artist": ""}}
* List all playlists. {{"playlist": "", "song": "", "artist": ""}}
* Create a playlist named favorites. {{"playlist": "favorites", "song": "", "artist": ""}}
* Add Bohemian Rhapsody to rock. {{"playlist": "rock", "song": "Bohemian Rhapsody", "artist": ""}}
* Delete Bohemian Rhapsody from rock. {{"playlist": "rock", "song": "Bohemian Rhapsody", "artist": ""}}
* Search for Bohemian Rhapsody. {{"playlist": "", "song": "Bohemian Rhapsody", "artist": ""}}
* Search for Bohemian Rhapsody by Queen. {{"playlist": "", "song": "Bohemian Rhapsody", "artist": "Queen"}}
* Recommend songs for rock. {{"playlist": "rock", "song": "", "artist": ""}}
* List songs in rock. {{"playlist": "rock", "song": "", "artist": ""}}
"""

get_questions_prompt = """
You are MusicAgent. Your task is to extract the intent and entities from the following input from a user: {inp}.
The possible intents are:

"""


def get_questions(inp: str) -> str:
    pass


def get_intent(inp: str) -> str:
    pass


def get_entities(inp: str, playlists: dict) -> tuple[str, dict]:
    try:
        intent_prompt = get_intent_prompt.format(inp=inp)
        entities_prompt = get_entities_prompt.format(
            inp=inp, playlists=playlists
        )
        intent = (
            ollama.generate(model, intent_prompt)["response"]
            .strip()
            .replace("\n", "")
        )
        intent = re.search(r"\(.*?\)", intent).group().strip("()")
        resp = (
            ollama.generate(model, entities_prompt)["response"]
            .strip()
            .replace("\n", "")
        )

        if "{" not in resp and "}" not in resp:
            return "I didn't understand that", {}
        return intent, {
            k: v
            for k, v in literal_eval(
                re.search(r"\{.*?\}", resp).group()
            ).items()
            if v
        }

    except Exception as e:
        print(e)
        return "I didn't understand that", {}


if __name__ == "__main__":
    print(get_entities("I want to create a playlist demo.", {}))
    print(
        get_entities(
            "Search for Creepin (with The Weeknd & 21 Savage) by Metro Boomin.",
            {},
        )
    )
    print(get_entities("Find Baby, It's Cold Outside (Christmas Edition).", {}))
    print(
        get_entities(
            "Show my playlists.",
            {
                "favorites": ["Bohemian Rhapsody", "Lose Yourself"],
                "rock": ["TnT", "Bohemian Rhapsody"],
            },
        )
    )
    print(
        get_entities(
            "i don't want the playlist favourites anymore.",
            {
                "favorites": ["Bohemian Rhapsody", "Lose Yourself"],
                "rock": ["TnT", "Bohemian Rhapsody"],
            },
        )
    )
