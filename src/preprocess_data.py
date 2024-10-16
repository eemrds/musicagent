import json
import tqdm

ORIGINAL_DATA_PATH = "/home/emrds/Downloads/release/mbdump/release"
NEW_DATA_PATH = "data/preprocessed"


def simplify_music_data(data):
    simplified_data = {
        "title": data.get("title"),
        "release_year": data.get("date"),
        "artist": {
            "name": data.get("artist-credit", [{}])[0]
            .get("artist", {})
            .get("name"),
            "id": data.get("artist-credit", [{}])[0]
            .get("artist", {})
            .get("id"),
            "aliases": [
                {"name": alias.get("name"), "type": alias.get("type")}
                for alias in data.get("artist-credit", [{}])[0]
                .get("artist", {})
                .get("aliases", [])
            ],
            "genres": [
                genre.get("name") for genre in data.get("genres", [])
            ],  # Extracting genre names
        },
        "tracks": [],
    }

    for media in data.get("media", []):
        for track in media.get("tracks", []):
            simplified_track = {
                "title": track.get("title"),
                "length": track.get("length"),
                "track_number": track.get("position"),
                "artist": track.get("artist-credit", [{}])[0]
                .get("artist", {})
                .get("name"),
                "genres": [
                    genre.get("name")
                    for genre in track.get("recording", {}).get("genres", [])
                ],  # Extracting genre names
            }
            simplified_data["tracks"].append(simplified_track)

    return simplified_data


with open(NEW_DATA_PATH, "a") as new:
    with open(ORIGINAL_DATA_PATH, "r") as original:
        for line in tqdm.tqdm(original):
            data = simplify_music_data(json.loads(line))

            new.write(f"{json.dumps(data)}\n")
