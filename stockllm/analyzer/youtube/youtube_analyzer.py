import os
import re

import OpenAI
import yt_dlp
from pydub import AudioSegment

from stockllm.analyzer.base_analyzer import BaseAnalyzer
from stockllm.common.logger import logger

# import json
# from youtube_transcript_api import YouTubeTranscriptApi


class YoutubeAnalyzer(BaseAnalyzer):
    def __init__(self) -> None:
        super().__init__()


MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes
INITIAL_CHUNK_DURATION = 10 * 60 * 1000  # 10 minutes in milliseconds


def extract_playlist_id(url):
    """Extract playlist ID from a YouTube playlist URL."""
    playlist_id_match = re.search(r"(?:list=)([a-zA-Z0-9_-]+)", url)
    return playlist_id_match.group(1) if playlist_id_match else None


def download_audio(video_id):
    audio_file = f"{video_id}.mp3"
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": audio_file,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Error processing video {video_id}: {e}")
        return None


def process_and_transcribe_audio(audio_file):
    """Process audio file, chunk if necessary, and transcribe"""
    try:
        audio = AudioSegment.from_mp3(audio_file)
        file_size = os.path.getsize(audio_file)

        if file_size > MAX_FILE_SIZE:
            logger.info(
                f"Audio file size ({file_size / 1024 / 1024:.2f} MB) exceeds 25 MB. Chunking and compressing."
            )
            chunks = chunk_audio(audio)
        else:
            chunks = [audio]

        transcripts = []
        client = OpenAI()

        for i, chunk in enumerate(chunks):
            chunk_file = f"chunk_{i}.mp3"
            chunk.export(chunk_file, format="mp3", bitrate="64k")

            with open(chunk_file, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio, response_format="text"
                )
            transcripts.append(transcript)
            os.remove(chunk_file)

        full_transcript = " ".join(transcripts)
        os.remove(audio_file)  # Clean up the original audio file
        logger.info("Audio transcribed successfully")
        return {"data": full_transcript, "error": False}
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {"data": f"Error transcribing audio: {str(e)}", "error": True}


def get_chunk_size(chunk: AudioSegment) -> int:
    """
    Get the file size of an AudioSegment chunk.

    Args:
    chunk (AudioSegment): The audio chunk.

    Returns:
    int: Size of the chunk in bytes.
    """
    temp_file = "temp_chunk.mp3"
    chunk.export(temp_file, format="mp3", bitrate="64k")
    size = os.path.getsize(temp_file)
    os.remove(temp_file)
    return size


def chunk_audio(
    audio: AudioSegment,
    max_size: int = MAX_FILE_SIZE,
    initial_duration: int = INITIAL_CHUNK_DURATION,
) -> list:
    chunks = []
    start = 0
    chunk_duration = initial_duration

    while start < len(audio):
        # Create a chunk of the current duration
        end = min(start + chunk_duration, len(audio))
        chunk = audio[start:end]

        # Check if the chunk size exceeds the maximum allowed size
        if get_chunk_size(chunk) > max_size:
            # If too large, reduce duration and try again
            chunk_duration = int(chunk_duration * 0.9)
            continue

        # If the chunk is acceptable, add it to the list and move to the next portion of audio
        chunks.append(chunk)
        start = end
        chunk_duration = initial_duration  # Reset chunk duration for the next iteration

    return chunks
