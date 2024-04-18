import json
import os.path
from multiprocessing import Pool, freeze_support
from quiz_dataset_songs_tools.extract_voice import extract_voice
from quiz_dataset_songs_tools.select_sample import make_track_sample_by_voice

input_tracks_index = "output/popular_youtube_2/tracks/index.json"
output_samples_dir = "output/popular_youtube_2/samples"


def load_tracks_index():
    with open(input_tracks_index) as f:
        return json.load(f)


def get_track_name(track_file_path: str) -> str:
    track_file_name = track_file_path.split("/")[-1]
    return track_file_name[:-4]


def sample_one_track(track_file_path: str, dest_dir: str):
    track_name = get_track_name(track_file_path)
    voice_file_path = f"{dest_dir}/{track_name}.voice.wav"
    if not os.path.exists(voice_file_path):
        print(f"Extract voice from {track_file_path} into {voice_file_path}")
        extract_voice(track_file_path, voice_file_path)
    sample_file_path = f"{dest_dir}/{track_name}.sample.mp3"
    if not os.path.exists(sample_file_path):
        print(f"Make sample out of {track_file_path} into {sample_file_path}")
        make_track_sample_by_voice(track_file_path, voice_file_path, sample_file_path)
    return {"sample_file": sample_file_path}


def sample_by_track_index(track_index, dest_dir: str):
    tracks = []
    sample_args = []
    for track in track_index:
        track_file_path = track.get("track_file")
        if not track_file_path:
            continue
        tracks.append(track)
        sample_args.append((track_file_path, dest_dir))
        # sample_one_track(track_file_path, dest_dir)

    with Pool(processes=5) as pool:
        results = pool.starmap(sample_one_track, sample_args)

    sample_index = []
    for i, result in enumerate(results):
        result.update(tracks[i])
        sample_index.append(result)
    return sample_index


def save_index(index, dest_dir):
    index_file_path = f"{dest_dir}/index.json"
    print(f"Save index to {index_file_path}")
    with open(index_file_path, "w") as f:
        f.write(json.dumps(index, indent=4))


if __name__ == "__main__":
    freeze_support()
    tracks_index = load_tracks_index()
    sample_index = sample_by_track_index(tracks_index, output_samples_dir)
    save_index(sample_index, output_samples_dir)
