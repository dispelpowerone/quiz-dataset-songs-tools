import openai
import re
import os.path
from dataclasses import dataclass
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)
from quiz_dataset_songs_tools.config import config


@dataclass
class SimilarSong:
    title: str
    artist: str


class Adviser:
    SIMILAR_SONG_RE = re.compile(
        '^\d[\.\)]\s+["”]([^"]+)["”]\s+(by|-|–)\s+([^\-\n]+)', re.M
    )

    def __init__(self, cache_dir: str):
        self._cache_dir = cache_dir
        self._gpt_model = "gpt-4"
        # self._gpt_model = "gpt-3.5-turbo"

    def get_similar_songs(
        self, title: str, artist: str, cache_key: str
    ) -> list[SimilarSong]:
        request = f'Give me four songs that can be mistaken for "{title}" by {artist}. Omit {artist} songs.'
        result_raw = self._get_from_cache(cache_key, "similar_songs")
        if not result_raw:
            result_raw = self._get(request)
            self._save_to_cache(cache_key, "similar_songs", result_raw)
        result = Adviser.SIMILAR_SONG_RE.findall(result_raw)
        similar_songs = []
        for entry in result:
            similar_songs.append(SimilarSong(entry[0], entry[2]))
        if len(similar_songs) != 4:
            print(similar_songs)
            raise Exception(f"Melformed GPT response: {result_raw}")
        return similar_songs

    def get_interesting_fact(self, title: str, artist: str, cache_key: str) -> str:
        request = f'Give me a short interesting fact about the song "{title}" by {artist} without mentioning song name and any artist names.'
        result_raw = self._get_from_cache(cache_key, "interesting_fact")
        if not result_raw:
            result_raw = self._get(request)
            self._save_to_cache(cache_key, "interesting_fact", result_raw)
        return result_raw

    def _get_from_cache(self, cache_key: str, cache_group: str) -> str | None:
        cache_file_path = f"{self._cache_dir}/{cache_key}.gpt.{cache_group}.txt"
        if not os.path.exists(cache_file_path):
            return None
        with open(cache_file_path) as f:
            return f.read()

    def _save_to_cache(self, cache_key: str, cache_group: str, data: str) -> None:
        cache_file_path = f"{self._cache_dir}/{cache_key}.gpt.{cache_group}.txt"
        with open(cache_file_path, "w") as f:
            f.write(data)

    def _get(self, request: str) -> str:
        result = self._ask_gpt(request)
        # Strip noice
        result = result.strip('" ')
        return result

    def _ask_gpt(self, request) -> str:
        messages = [
            {
                "role": "system",
                "content": request,
            }
        ]
        chat = _chat_completion_with_backoff(model=self._gpt_model, messages=messages)
        print(f"paraphrase::_ask_gpt: {request} -> {chat.choices[0].message.content}")
        return chat.choices[0].message.content


client = OpenAI(
    api_key=config["openai"]["api_key"],
)


@retry(
    retry=retry_if_exception_type(
        (
            # openai.APIError,
            # openai.APIConnectionError,
            # openai.RateLimitError,
            # openai.Timeout,
        )
    ),
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(1),
)
def _chat_completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)
