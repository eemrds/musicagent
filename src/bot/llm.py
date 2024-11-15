import ast
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
* song_release: Search for release date of a song.
* artist_album_count: Search for the number of albums by an artist.
* delete_song_positional: Delete a song from a playlist by position.
* add_song_positional: Add a song to a playlist by position.
* add_artist: Simulator called function to add songs to a playlist.
* add_song_simulation: Simulator called function to add songs to a playlist.

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
* Delete Lose Yourself from rock. (delete_song)
* Recommend songs for rock. (recommend_songs)
* Search for release date of Bohemian Rhapsody. (song_release)
* Search for the number of albums by Queen. (artist_album_count)
* Delete the first song from rock. (delete_song_positional)
* Delete the last two songs from rock. (delete_song_positional)
* Search for Bohemian Rhapsody by Queen and add the first result to rock. (add_song_positional)
* Search for Bohemian Rhapsody by Queen and add the last two results to rock. (add_song_positional)
* Add artist Queen to rock. (add_artist)
* Add artist Eminem to top10. (add_artist)
* Add song Bohemian Rhapsody to rock as simulation. (add_song_simulation)
* Add song Lose Yourself to rap as simulation. (add_song_simulation)
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
* When was Free bird released. {{"playlist": "", "song": "Bohemian Rhapsody", "artist": ""}}
* When was Free bird by Lynyrd Skynyrd released. {{"playlist": "", "song": "Free bird", "artist": "Lynyrd Skynyrd"}}
* Search for the number of albums by Queen. {{"playlist": "", "song": "", "artist": "Queen"}}
* Search for songs by Queen. {{"playlist": "", "song": "", "artist": "Queen"}}
* Delete Lose Yourself from rock. {{"playlist": "rock", "song": "Lose Yourself", "artist": ""}}
* Delete the first song from rock. {{"playlist": "rock", "song": "", "artist": ""}}
* Delete the last two songs from rock. {{"playlist": "rock", "song": "", "artist": ""}}
* Search for Bohemian Rhapsody by Queen and add the first result to rock. {{"playlist": "rock", "song": "", "artist": ""}}
* Search for Bohemian Rhapsody by Queen and add the last two results to rock. {{"playlist": "rock", "song": "", "artist": ""}}
* Add artist Coolio to playlist chill. {{"playlist": "chill", "song": "", "artist": "Coolio"}}
* Add artist Queen to playlist top10. {{"playlist": "top10", "song": "", "artist": "Queen"}}
* Add song Bohemian Rhapsody to rock as simulation. {{"playlist": "rock", "song": "Bohemian Rhapsody", "artist": ""}}
* Add song Lose Yourself to rap as simulation. {{"playlist": "rap", "song": "Lose Yourself", "artist": ""}}
"""

number_entities_prompt = """
You are MusicAgent. Your task is to extract the number from the following input from a user: {inp}.
Return the number as an integer. DO NOT include any other text.
Type the number in the following format: (number)

Examples:
* Simulate a playlist with 5 songs. (5)
* Simulate a new playlist called favorites with 10 songs. (10)
* Simulate a playlist with 15 songs. (15)
"""


positional_entities_prompt = """
You are MusicAgent. Your task is determine the number of songs from the following input from a user: {inp}.


Return the number of songs to delete as an integer in parentheses. DO NOT include any other text.
Type the entities in the following format: (number)

Examples:
* Delete the first song from rock. (1)
* Delete the last two songs from rock. (2)
* Search for Travelling and add the first result to rock. (1)
* Search for Bohemian Rhapsody by Queen and add the last two results to rock. (2)
* Search for the release date of the first song in test. (1)
* Search for the release date of the last two songs in test. (2)
"""


# Examples:
# * Delete the first song from rock. Playlist: [{{"title": "Travelling Man", "artist": "DJ Shadow", "album": "Deck Safari}}, {{"title": "Travelling Through the Dark", "artist": "William Stafford", "album": "Traveling Through the Dark"}}, {{"title": "Travelling Light", "artist": "Talib Kweli", "album": "Rocket Ships"}}]. ["Travelling Man"]
# * Delete the last two songs from rock. Playlist: [{{"title": "Travelling Man", "artist": "DJ Shadow", "album": "Deck Safari}}, {{"title": "Travelling Through the Dark", "artist": "William Stafford", "album": "Traveling Through the Dark"}}, {{"title": "Travelling Light", "artist": "Talib Kweli", "album": "Rocket Ships"}}]. ["Travelling Through the Dark", "Travelling Light"]
# * Search for Travelling and add the first result to rock. Playlist: [{{"title": "Travelling Man", "artist": "DJ Shadow", "album": "Deck Safari}}, {{"title": "Travelling Through the Dark", "artist": "William Stafford", "album": "Traveling Through the Dark"}}, {{"title": "Travelling Light", "artist": "Talib Kweli", "album": "Rocket Ships"}}]. ["Travelling Man"]
# * Search for Bohemian Rhapsody by Queen and add the last two results to rock. Playlist: [{{"title": "Travelling Man", "artist": "DJ Shadow", "album": "Deck Safari}}, {{"title": "Travelling Through the Dark", "artist": "William Stafford", "album": "Traveling Through the Dark"}}, {{"title": "Travelling Light", "artist": "Talib Kweli", "album": "Rocket Ships"}}]. ["Travelling Through the Dark", "Travelling Light"]
# * Search for the release date of the first song in rock. Playlist: [{{"title": "Travelling Man", "artist": "DJ Shadow", "album": "Deck Safari}}, {{"title": "Travelling Through the Dark", "artist": "William Stafford", "album": "Traveling Through the Dark"}}, {{"title": "Travelling Light", "artist": "Talib Kweli", "album": "Rocket Ships"}}]. ["Travelling Man"]

get_questions_prompt = """
You are MusicAgent. Your task is to extract the intent and entities from the following input from a user: {inp}.
The possible intents are:

"""


def get_number(inp: str) -> int:
    try:
        prompt = number_entities_prompt.format(inp=inp)
        resp = (
            ollama.generate(model, prompt)["response"].strip().replace("\n", "")
        )
        return int(re.search(r"\(.*?\)", resp).group().strip("()"))

    except Exception as e:
        return 5


def get_position(inp: str, playlist: list[str]) -> list[str]:
    try:
        prompt = positional_entities_prompt.format(inp=inp, playlists=playlist)
        resp = (
            ollama.generate(model, prompt)["response"].strip().replace("\n", "")
        )
        number = ast.literal_eval((re.search(r"\(.*?\)", resp)).group())
        if "first" in inp:
            return playlist[:number]
        elif "last" in inp:
            return playlist[-number:]

    except Exception as e:
        print(e)
        return []


def get_entities(inp: str, playlists: dict = {}) -> tuple[str, dict]:
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
