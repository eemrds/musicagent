import json
import tqdm

ORIGINAL_DATA_PATH = "/home/emrds/Downloads/release/mbdump/release"
NEW_DATA_PATH = "data/preprocessed"


def simplify_music_data(data):

    item = json.loads(data)
    songs = []

    for media in item.get("media", []):
        for track in media.get("tracks", []):
            if not track.get("recording").get("title"):
                continue
            song = {
                "title": track.get("recording", {}).get("title", "Unknown"),
                "artist": track.get("recording", {})
                .get("artist-credit", [{}])[0]
                .get("artist", {})
                .get("name", None),
                "release": track.get("recording", {}).get(
                    "first-release-date", None
                )[:4],
                "album": item.get("release-group", {}).get("title", None),
                "genre": track.get("recording", {}).get("genre", []),
                "length": track.get("recording", {}).get("length", None),
            }
            print(song)
            songs.append(song)
    return songs


with open(NEW_DATA_PATH, "a") as new:
    with open(ORIGINAL_DATA_PATH, "r") as original:
        for line in tqdm.tqdm(original):
            songs = simplify_music_data(json.loads(line))
            for song in songs:
                data = {
                    "title": song.get("title"),
                    "artist": song.get("artist"),
                    "album": song.get("album"),
                    "year": song.get("release"),
                    "genre": song.get("genre"),
                }
                new.write(json.dumps(data) + "\n")
