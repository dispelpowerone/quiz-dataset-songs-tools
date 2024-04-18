import json
from quiz_dataset_songs_tools.gpt import Adviser


input_samples_index_path = 'output/popular_youtube_2/samples/index.json'
output_dir = 'output/popular_youtube_2/questions'
advicer = Adviser(cache_dir=output_dir)


class ErrorLog:
    def __init__(self, output_dir):
        self._output_dir = output_dir

    def save(self, key: str, error):
        file_path = f'{self._output_dir}/{key}.error.txt'
        print(f'Log an error to {file_path}')
        with open(file_path, 'w') as f:
            f.write(str(error))


error_log = ErrorLog(output_dir=output_dir)


def load_sample_index():
    with open(input_samples_index_path) as f:
        return json.load(f)


def save_index(index, dest_dir):
    index_file_path = f'{dest_dir}/index.json'
    print(f'Save index to {index_file_path}')
    with open(index_file_path, 'w') as f:
        f.write(json.dumps(index, indent=4))


def get_track_name(track_file_path: str) -> str:
    track_file_name = track_file_path.split('/')[-1]
    return track_file_name[:-4]


def questions_for_sample(sample):
    track_name = get_track_name(sample['track_file'])
    track_title = sample['title']
    track_artist = sample['artist']
    try:
        print(f'Get similar songs for "{track_title}" by {track_artist}')
        similar_songs = advicer.get_similar_songs(track_title, track_artist, track_name)
        print(f'Got: {similar_songs}')
        answers = [f'"{track_title}" by {track_artist}']
        for song in similar_songs:
            answers.append(f'"{song.title}" by {song.artist}')
        print(f'Get interesting fact about "{track_title}" by {track_artist}')
        # interesting_fact = advicer.get_interesting_fact(track_title, track_artist, track_name)
        interesting_fact = None
        question = {
            'question': interesting_fact,
            'answers': answers,
        }
        question.update(sample)
        return question
    except Exception as e:
        error_log.save(track_name, e)
        raise e


def questions_by_sample_index(sample_index):
    questions = []
    for sample in sample_index:
        question = questions_for_sample(sample)
        if question:
            questions.append(question)
    return questions


sample_index = load_sample_index()
questions = questions_by_sample_index(sample_index)
save_index(questions, output_dir)
