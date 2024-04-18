import json
import urllib.request
import unicodedata
import re
import os.path
import csv
import requests
import subprocess
import shutil
from yandex_music import Client
from yandex_music.utils.request import Request
from quiz_dataset_songs_tools.config import config


token = config["api.music.yandex"]["token"]
request = None

client = Client(token, request=request, base_url='https://api.music.yandex.ru').init()
#search_result = client.search('"Like a Rolling Stone" by Bob Dylan')
#print(search_result)
#print(client.tracks_download_info(track_id=93729058, get_direct_links=True))

def search_artist(artist: str):
    return client.search(f'{artist}')

def search_track(title: str, artist: str):
    return client.search(f'{title} {artist}')

def select_artist_id(search_result) -> int:
    if not search_result.artists:
        return None
    return search_result.artists.results[0].id

def search_artist_id(artist: str):
    artist_id = select_artist_id(search_artist(artist))
    if artist_id is not None:
        return artist_id
    for sep in [" ft. "]:
        if sep not in artist:
            continue
        primary_artist = artist.split(sep)[0].strip()
        artist_id = select_artist_id(search_artist(primary_artist))
        if artist_id is not None:
            return artist_id
    raise Exception('No artist found')

def select_track_id(search_result, artist_id: int) -> int:
    if not search_result.tracks:
        raise Exception('No tracks found')
    best_by_likes = None
    best_by_likes_value = 5
    best_by_year = None
    best_by_year_value = 2025
    best_by_order = None
    for track in search_result.tracks.results:
        """
        print('---')
        print(f'track.title : {track.title}')
        print(f'track.version : {track.version}')
        print(f'album.title : {album.title}')
        print(f'album.year : {album.year}')
        print(f'album.type : {album.type}')
        print(f'album.likes_count : {album.likes_count}')
        """
        # Filter by artist id
        artist_found = False
        for artist in track.artists:
            if artist.id == artist_id:
                artist_found = True
        if not artist_found:
            continue
        # Try to skip remix, live and karaoke
        if track.version:
            version = track.version.lower()
            version_has_stop_words = False
            for stop_word in ['live', 'tour', 'remix', 'karaoke']:
                if stop_word in version:
                    version_has_stop_words = True
            if version_has_stop_words:
                continue
        # Select the best by number of likes and release year
        album = track.albums[-1]
        if album.likes_count is not None and album.likes_count > best_by_likes_value:
            best_by_likes = track
            best_by_likes_value = album.likes_count
        if album.year is not None and album.year < best_by_year_value:
            best_by_year = track
            best_by_year_value = album.year
        if not best_by_order:
            best_by_order = track
    if best_by_likes:
        return best_by_likes.id
    if best_by_year:
        return best_by_year.id
    if best_by_order:
        return best_by_order.id
    raise Exception(f'No proper tracks found: {str(search_result.tracks)}')

def get_download_link(track_id: int) -> str:
    download_options = client.tracks_download_info(
        track_id=track_id,
        get_direct_links=True
    )
    for option in download_options:
        if option.codec != 'mp3':
            continue
        if option.bitrate_in_kbps != 192:
            continue
        return option.direct_link

def download_track(track_link: str, file_name: str):
    subprocess.run([f'curl -vvv --max-time 60 --retry 3 --output {file_name} -H @headers.txt {track_link}'],
        shell=True,
    )
    #urllib.request.urlretrieve(track_link, file_name)
    #with urllib.request.urlopen(track_link) as response:
    #    shutil.copyfileobj(response, open(file_name, 'w'))

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def save_search_result(search_result, dest_file_path: str):
    with open(dest_file_path, 'w') as f:
        f.write(str(search_result))

def save_error(e, dest_file_path: str):
    print(f'Log an error to {dest_file_path}')
    with open(dest_file_path, 'w') as f:
        f.write(str(e))

def retrieve_one_song(title: str, artist: str, track_file: str, src_dir: str, dest_dir: str) -> None:
    dest_file_id = slugify(f'{title}_by_{artist}')
    dest_file_path = f'{dest_dir}/{dest_file_id}.mp3'
    if os.path.exists(dest_file_path):
        return { 'track_file': dest_file_path, 'error_file': None }
    if track_file:
        retrieve_from_source(track_file, src_dir, dest_file_path)
        return { 'track_file': dest_file_path, 'error_file': None }
    dest_err_file_path = f'{dest_dir}/{dest_file_id}.error.txt'
    dest_sr_file_path = f'{dest_dir}/{dest_file_id}.search_results.txt'
    if os.path.exists(dest_err_file_path):
        return { 'track_file': None, 'error_file': dest_err_file_path }
    print(f'Retreive "{title}" by {artist} into {dest_file_path}')
    try:
        artist_id = search_artist_id(artist)
        track_search_result = search_track(title, artist)
        save_search_result(track_search_result, dest_sr_file_path)
        track_id = select_track_id(track_search_result, artist_id)
        track_link = get_download_link(track_id)
        download_track(track_link, dest_file_path)
    except Exception as e:
        save_error(e, dest_err_file_path)
        return { 'track_file': None, 'error_file': dest_err_file_path }
    return { 'track_file': dest_file_path, 'error_file': None }

def retrieve_from_source(src_file_name: str, src_dir: str, dest_file_path: str) -> None:
    src_file_path = f'{src_dir}/{src_file_name}'
    shutil.copyfile(src_file_path, dest_file_path)

def load_songs_list(file_path: str):
    songs_list = []
    with open(file_path, encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)
        artist_column_index = header.index('artist')
        title_column_index = header.index('title')
        track_column_index = header.index('track')
        for row in reader:
            artist = normalize_text(row[artist_column_index])
            title = normalize_text(row[title_column_index])
            track = row[track_column_index].strip()
            songs_list.append((title, artist,track))
    return songs_list

def normalize_text(text: str) -> str:
    text = text.strip()
    text = text.replace('á', 'a')
    text = text.replace('é', 'e')
    text = text.replace('’', '\'')
    text = text.replace('í', 'i')
    text = text.replace('ó', 'o')
    return text

def retrieve_from_list(songs_list, src_dir, dest_dir):
    index = []
    for title, artist, track_file in songs_list:
        result = retrieve_one_song(title, artist, track_file, src_dir, dest_dir)
        index.append({
            'title': title,
            'artist': artist,
            'track_file': result['track_file'],
            'error_file': result['error_file'],
        })
    return index

def save_index(index, dest_dir):
    index_file_path = f'{dest_dir}/index.json'
    print(f'Save index to {index_file_path}')
    with open(index_file_path, 'w') as f:
        f.write(json.dumps(index, indent=4))

songs_list = load_songs_list('lists/popular_youtube_2.csv')
index = retrieve_from_list(songs_list, 'input/popular_youtube_2', 'output/popular_youtube_2/tracks')
save_index(index, 'output/popular_youtube_2/tracks')
