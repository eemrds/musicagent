import os
from typing import Optional, Union

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

CLIENT = MongoClient(
    "mongodb+srv://martinerik99:ug5uzVjD3UjYJ3VW@dat640.ehx2a.mongodb.net/?retryWrites=true&w=majority&appName=DAT640"
)
DB = CLIENT["musicDB"]
USERS_COLLECTION = DB["users"]
SONG_COLLECTION = DB["songs"]


class Song:
    """Song class"""

    def __init__(
        self,
        title: str,
        artist: Optional[str],
        album: Optional[str],
        year: Optional[int],
        genre: Optional[str],
    ):
        self.title = title
        self.artist = artist
        self.album = album
        self.year = year
        self.genre = genre

    def __repr__(self):
        return self.dump()

    def __str__(self):
        return str(self.dump())

    def dump(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "year": self.year,
            "genre": self.genre,
        }


class Songs(list):
    """Songs class"""

    def __init__(self, songs: list[dict]):
        super().__init__([Song(**s) for s in songs])

    def __repr__(self):
        return self.dump()

    def __str__(self):
        return str(self.dump())

    def __contains__(self, item_name):
        return item_name in [s.title for s in self]

    def get(self, item_name) -> Song:
        return filter(lambda s: s.title == item_name, self)[0]

    def add(self, song: dict) -> "Songs":
        self.append(Song(**song) if isinstance(song, dict) else song)
        return self

    def remove(self, song_name: str) -> "Songs":
        self = [s for s in self if s.title != song_name]
        return self

    def dump(self) -> list[dict]:
        return [s.dump() for s in self]


class Playlist:
    """Playlist class"""

    def __init__(self, name: str, songs: list[dict] = []):
        self.name = name
        self.songs = Songs(songs)

    def __repr__(self):
        return self.dump()

    def __str__(self):
        return str(self.dump())

    def add(self, song: Song) -> "Playlist":
        self.songs.add(song)
        return self

    def remove(self, song_name: str) -> "Playlist":
        self.songs = self.songs.remove_song(song_name)
        return self

    def dump(self) -> dict[str, list[dict]]:
        return {"name": self.name, "songs": self.songs.dump()}


class Playlists(list):
    """Playlists class"""

    def __init__(self, playlists: list[dict]):
        super().__init__([Playlist(**p) for p in playlists])

    def __repr__(self):
        return self.dump()

    def __str__(self):
        return str(self.dump())

    def __contains__(self, item_name):
        return item_name in [p.name for p in self]

    def get(self, item_name) -> Playlist:
        return list(filter(lambda p: p.name == item_name, self))[0]

    def add(self, playlist: Union[dict, Playlist]) -> "Playlists":
        if isinstance(playlist, Playlist):
            self.append(playlist)
        else:
            self.append(Playlist(**playlist))
        return self

    def remove(self, playlist_name: str) -> "Playlists":
        self = [p for p in self if p.name != playlist_name]
        return self

    def dump(self) -> list[dict[str, list[dict]]]:
        return [p.dump() for p in self]


class User:
    """User class"""

    def __init__(
        self,
        username: str,
        email: Optional[str] = None,
        playlists: list[dict] = [],
    ):
        self.username = username
        self.email = email
        self.playlists = Playlists(playlists)

    def __repr__(self):
        return self.dump()

    def __str__(self):
        return str(self.dump())

    def add_playlist(self, playlist: Playlist):
        self.playlists.append(playlist)

    def remove_playlist(self, playlist_name: str) -> "User":
        self.playlists = [p for p in self.playlists if p.name != playlist_name]
        return self

    def dump(self) -> dict:
        return {
            "username": self.username,
            "email": self.email,
            "playlists": [p.dump() for p in self.playlists],
        }

    def update_db(self):
        USERS_COLLECTION.update_one(
            {"username": self.username},
            {"$set": self.dump()},
        )


def update_db(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.user.update_db()

    return wrapper


class MusicDB:
    """Music database class"""

    def __init__(self, user: User):
        self.user = user

    def get_playlists(self) -> Playlists:
        """Get playlists of the user."""
        return self.user.playlists if self.user else None

    def get_playlist(self, playlist_name: str) -> Playlist:
        """Get playlist by name."""
        if playlist_name not in self.user.playlists:
            raise ValueError("Playlist not found.")
        return self.user.playlists.get(playlist_name)

    @update_db
    def add_playlist(self, playlist_name: str) -> Playlists:
        """Add playlist to the user."""
        if playlist_name in self.user.playlists:
            raise ValueError("Playlist already exists.")
        self.user.playlists = self.user.playlists.add(Playlist(playlist_name))
        return self.user.playlists

    @update_db
    def remove_playlist(self, playlist_name: str) -> str:
        """Remove playlist from the user."""
        self.user.playlists = self.user.playlists.remove(playlist_name)
        return f"Playlist {playlist_name} deleted."

    @update_db
    def get_song_from_playlist(
        self, playlist_name: str, song_name: str
    ) -> Song:
        """Get song from the playlist."""
        if playlist_name not in self.user.playlists:
            raise ValueError("Playlist not found.")
        return self.user.playlists.get(playlist_name).songs.get(song_name)

    @update_db
    def add_songs_to_playlist(
        self, song: Union[dict, Song], playlist_name: str
    ) -> list[Playlist]:
        """Add song to the playlist."""
        if playlist_name not in self.user.playlists:
            raise ValueError("Playlist not found.")
        self.user.playlists.extend(
            [
                self.user.playlists.get(playlist_name).add(
                    Song(**song) if isinstance(song, dict) else song
                )
            ]
        )
        return self.user.playlists

    @update_db
    def add_song_to_playlist(
        self, song: Union[dict, Song], playlist_name: str
    ) -> Playlist:
        """Add song to the playlist."""
        # Ensure the playlist exists
        if playlist_name not in self.user.playlists:
            raise ValueError("Playlist not found.")
        
        # Get the playlist
        playlist = self.user.playlists.get(playlist_name)
        
        # Add the song to the playlist
        playlist.add(Song(**song) if isinstance(song, dict) else song)
        
        # Return the updated playlist (or just None if not needed)
        return playlist

    @update_db
    def remove_song_from_playlist(
        self, song_name: str, playlist_name: str
    ) -> list[Playlist]:
        """Remove song from the playlist."""
        if playlist_name not in self.user.playlists:
            raise ValueError("Playlist not found.")
        self.user.playlists = self.user.playlists.get(playlist_name).remove(
            song_name
        )
        return self.user.playlists

def search_specific_song(song_name: str, artist: Optional[str] = None) -> Optional[Song]:
    """Search for a specific song by name, optionally filtering by artist."""

    query = {"title": song_name}
    if artist is not None:
        query["artist"] = artist

    result = SONG_COLLECTION.find_one(query)
    
    if not result:
        return None  # Return None if no song is found

    result.pop("_id", None)  # Remove _id if present
    
    return Song(**result)  # Return a single Song object

def search_song(song_name: str, artist: Optional[str] = None) -> Song:
    """Search for song by name."""

    query = (
        {"$text": {"$search": f"{song_name} {artist}"}}
        if artist
        else {"$text": {"$search": song_name}}
    )

    results = list(
        SONG_COLLECTION.find(query)
    )
    if not results:
        return Songs([])
    for result in results:
        result.pop("_id")
    return Songs(results)


def search_album_release(album_name: str) -> str:
    """Search for album release year by name."""
    result = SONG_COLLECTION.find_one(
        {"album": {"$regex": album_name, "$options": "i"}}
    )
    if not result:
        return "Unknown"
    return result["year"]


def search_artist_albums(artist_name: str) -> list[str]:
    """Search for artist albums by name."""
    artist = SONG_COLLECTION.find_one(
        {"artist": {"$regex": artist_name, "$options": "i"}}
    )
    results = list(SONG_COLLECTION.find({"artist": artist}))
    if not results:
        return []
    return [result["album"] for result in results]


def QueryDB(query: dict) -> list[dict]:
    """Query the database."""
    results = list(SONG_COLLECTION.find(query))
    for result in results:
        result.pop("_id")
    return results


def get_user(username) -> User:
    """Get user by username."""
    db_user = USERS_COLLECTION.find_one({"username": username})
    if not db_user:
        raise ValueError("User not found.")
    return User(
        username=db_user["username"],
        email=db_user["email"],
        playlists=db_user["playlists"],
    )


def add_user(username: str, email: Optional[str]) -> User:
    """Add user to the database."""
    db_user = USERS_COLLECTION.find_one({"username": username})
    if db_user:
        raise ValueError("User already exists.")

    user = User(username=username, email=email)
    USERS_COLLECTION.insert_one(user.dump())
    return user
