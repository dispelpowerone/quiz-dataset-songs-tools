import scipy.io.wavfile
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment

def select_voice_sample(voice_file_path: str, sample_duration: str) -> int:
    sampleRate, audioBuffer = scipy.io.wavfile.read(voice_file_path)
    duration = int(len(audioBuffer) / sampleRate)

    #minValue = np.min(audioBuffer)
    maxValue = np.max(audioBuffer)
    #print(f'min = {minValue}, max = {maxValue}')

    #plt.plot(audioBuffer)
    #plt.show()

    rangeSize = maxValue #- minValue
    audioBuffer = np.clip(
        audioBuffer,
        0, # minValue + rangeSize * 0.2,
        maxValue - rangeSize * 0.2
    )

    #plt.plot(audioBuffer)
    #plt.show()

    sumBuffer = np.cumsum(audioBuffer)

    sampleSize = sample_duration
    bestSampleOffset = 0
    bestSampleSum = 0
    for i in range(0, duration - sampleSize):
        begin = i * sampleRate
        end = (i + sampleSize) * sampleRate
        sampleSum = sumBuffer[end] - sumBuffer[begin]
        if sampleSum > bestSampleSum:
            bestSampleSum = sampleSum
            bestSampleOffset = i

    print(f'Track duration {duration}. Best sample offset {int(bestSampleOffset / 60)}:{bestSampleOffset % 60}')

    return bestSampleOffset

def cut_track_sample(track_file_path: str, offset_sec: int, duration_sec: int, sample_file_path: str):
    try:
        track = AudioSegment.from_mp3(track_file_path)
    except:
        track = AudioSegment.from_file(track_file_path, "mp4")
    track_sample_start = offset_sec * 1000
    track_sample_end = track_sample_start + duration_sec * 1000
    track_sample = track[track_sample_start:track_sample_end]
    track_sample.export(sample_file_path, format='mp3')

def make_track_sample_by_voice(track_file_path: str, voice_file_path: str, sample_file_path: str) -> str:
    sample_duration = 15
    sample_offset = select_voice_sample(voice_file_path, sample_duration)
    cut_track_sample(track_file_path, sample_offset, sample_duration, sample_file_path)
