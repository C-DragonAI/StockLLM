import json
import os
import re
from typing import Any, Dict, List, Optional

import openai
import requests
import yt_dlp
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptAvailable, TranscriptsDisabled

from stockllm.analyzer.base_analyzer import BaseAnalyzer
from stockllm.common.logger import logger

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes
INITIAL_CHUNK_DURATION = 10 * 60 * 1000  # 10 minutes in milliseconds


class InvalidYoutubeVideoURL(Exception):
    """Custom exception to represent an invalid YouTube video URL"""

    pass


class TranscriptNotAvailableError(Exception):
    """Custom exception to represent that the transcript for a YouTube video is not available"""

    pass


class YoutubeAnalyzer(BaseAnalyzer):
    def __init__(self, configs_file: str, url: str) -> None:
        self.url = url
        super().__init__(configs_file)

    def load_configs(self, configs_file: str) -> Dict[str, Any]:
        """
        Load configurations from a JSON file.

        Args:
        configs_file (str): Path to the configuration file.

        Returns:
        Dict[str, Any]: Configuration dictionary.
        """
        default_config = {
            "output_dir": "youtube_output",
            "save_subtitle": True,
            "cookies_file": None,
            "username": None,
            "password": None,
            "openai_key": None,
            "max_retries": 1,
        }

        if not os.path.exists(configs_file):
            logger.warning(
                f"Config file {configs_file} not found. Using default configuration."
            )
            return default_config

        try:
            with open(configs_file, "r") as f:
                user_config = json.load(f)

            # Update default config with user-provided values
            config = {**default_config, **user_config}

            # Ensure output directory exists
            os.makedirs(config["output_dir"], exist_ok=True)
            self.client = openai.OpenAI(api_key=config["openai_key"])
            return config

        except json.JSONDecodeError:
            logger.error(
                f"Error parsing config file {configs_file}. Using default configuration."
            )
            return default_config
        except Exception as e:
            logger.error(
                f"Unexpected error loading config file {configs_file}: {str(e)}. Using default configuration."
            )
            return default_config

    def load_data(self):
        """Load data from a YouTube video or playlist.

        This method processes the URL stored in the object's 'url' attribute.
        It can handle both single video URLs and playlist URLs.

        Returns:
            Any: The result of processing the URL. This could be:
                - A dictionary containing information about a single video.
                - A list of dictionaries, each containing information about a video in a playlist.

        Raises:
            ValueError: If the object does not have a 'url' attribute.

        Note:
            This method internally calls the 'process_url' method to handle the actual URL processing.
        """
        print(self.url)
        if hasattr(self, "url"):
            return self.process_url(self.url)
        else:
            raise ValueError("URL not provided")

    def analysis(self):
        if not hasattr(self, "data"):
            self.data = self.load_data()
        # TODO: 使用 whisper 處理 transcript
        # 1. 載入音訊檔案
        # 2. 使用 whisper 模型進行轉錄
        # 3. 處理轉錄結果
        # 4. 儲存轉錄文本
        return self.data

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from a YouTube URL."""
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})",
            r"^([0-9A-Za-z_-]{11})$",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from a YouTube playlist URL."""
        playlist_id_match = re.search(r"(?:list=)([0-9A-Za-z_-]+)", url)
        return playlist_id_match.group(1) if playlist_id_match else None

    def get_ydl_opts(self, include_download_opts: bool = False) -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
        }
        if self.configs["cookies_file"]:
            ydl_opts["cookiefile"] = self.configs["cookies_file"]
        if self.configs["username"] and self.configs["password"]:
            ydl_opts["username"] = self.configs["username"]
            ydl_opts["password"] = self.configs["password"]

        if include_download_opts:
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        return ydl_opts

    def gget_video_info(self, url: str) -> Dict[str, str]:
        """Get video title and channel title from a YouTube URL."""
        ydl_opts = self.get_ydl_opts()
        for _ in range(self.configs["max_retries"]):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return {
                        "video_id": info["id"],
                        "video_title": info["title"],
                        "channel_title": info["channel"],
                    }
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"Error getting video info: {e}")
        return {}

    def get_playlist_info(self, url: str) -> List[Dict[str, str]]:
        ydl_opts = self.get_ydl_opts()
        ydl_opts["ignoreerrors"] = True
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return [
                    {
                        "video_id": entry["id"],
                        "video_title": entry["title"],
                        "channel_title": entry.get("channel", "Unknown Channel"),
                    }
                    for entry in info["entries"]
                    if "id" in entry and "title" in entry
                ]
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Error getting playlist info: {e}")
            return []

    def get_transcript(
        self,
        video_id: str,
        channel_title: str,
        video_title: str,
        save_subtitle: bool = False,
    ) -> Optional[List[Dict[str, str]]]:
        """
        Get transcript for a given YouTube video ID.

        Args:
        video_id (str): YouTube video ID
        save_subtitle (bool): Whether to save the subtitle to a file

        Returns:
        Optional[List[Dict[str, str]]]: List of transcript entries or None if not available
        """
        try:
            # Try to get the transcript in Chinese languages first
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["zh-TW", "zh-CN", "zh"],
                cookies=self.configs["cookies_file"],
            )
        except (TranscriptsDisabled, NoTranscriptAvailable):
            try:
                # If Chinese is not available, try to get any available transcript
                transcript = YouTubeTranscriptApi.get_transcript(
                    channel_title, cookies=self.configs["cookies_file"]
                )
            except Exception as e:
                logger.error(f"Error getting transcript for video {channel_title}: {e}")
                return None

        result = {
            "channel_id": channel_title,
            "video_title": video_title,
            "transcript": transcript,
        }

        if save_subtitle:
            subtitle_file = (
                f"{self.configs['output_dir']}/{channel_title}_subtitle.json"
            )
            with open(subtitle_file, "a+", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"Subtitle saved to {subtitle_file}")

        return result

    def download_audio(self, video_id: str) -> Optional[str]:
        audio_file = f"{self.configs['output_dir']}/{video_id}.mp3"
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
            return audio_file
        except yt_dlp.utils.DownloadError as e:
            try:
                # Thanks to Cobalt! Your work is truly great.
                # https://github.com/imputnet/cobalt
                logger.info("Initiating download using Cobalt API.")

                url = "https://olly.imput.net/api/json"
                params = {
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "isAudioOnly": True,
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }

                # Make the API request
                response = requests.post(url, json=params, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    download_url = result["url"]
                    # Step 2: Download the audio content from the stream
                    logger.info("Start to stream download using Cobalt API.")
                    with requests.get(download_url, stream=True) as stream_response:
                        stream_response.raise_for_status()
                        os.makedirs(self.configs["output_dir"], exist_ok=True)
                        with open(audio_file, "wb") as file:
                            for chunk in stream_response.iter_content(chunk_size=8192):
                                file.write(chunk)

                    logger.info("Download successful!")
                    return audio_file
            except ValueError:
                logger.error(f"Error processing video {video_id}: {e}")

            return None

    def process_and_transcribe_audio(
        self, video_info: Dict[str, str], audio_file: str
    ) -> Dict[str, Any]:
        """Process audio file, chunk if necessary, and transcribe using OpenAI API"""
        try:
            audio = AudioSegment.from_mp3(audio_file)
            transcripts = []
            start = 0

            while start < len(audio):
                end = min(start + INITIAL_CHUNK_DURATION, len(audio))

                while True:
                    chunk = audio[start:end]
                    chunk_file = os.path.join(
                        self.configs["output_dir"], "temp_chunk.mp3"
                    )
                    chunk.export(chunk_file, format="mp3", bitrate="64k")

                    if os.path.getsize(chunk_file) <= MAX_FILE_SIZE:
                        break

                    end = start + (end - start) // 2
                    os.remove(chunk_file)

                    if end - start < 1000:  # Minimum 1 second chunk
                        raise ValueError("Unable to create a small enough chunk")

                with open(chunk_file, "rb") as audio_chunk:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_chunk,
                        response_format="verbose_json",
                    )

                transcripts.extend(response.segments)
                os.remove(chunk_file)

                start = end

            result = {
                "video_id": video_info["video_id"],
                "video_title": video_info["video_title"],
                "channel_title": video_info["channel_title"],
                "transcript": [
                    {
                        "text": segment["text"],
                        "start": segment["start"],
                        "duration": segment["end"] - segment["start"],
                    }
                    for segment in transcripts
                ],
            }

            json_file = os.path.join(
                self.configs["output_dir"],
                f"{video_info['channel_title']}_{video_info['video_title']}_transcript.json",
            )
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"OpenAI transcript saved to {json_file}")
            return result

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {"video_id": video_info["video_id"], "error": str(e)}
        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)

    def process_single_video(self, url: str) -> Dict[str, Any]:
        """Process a single YouTube video from URL."""
        video_info = self.get_video_info(url)

        transcript = self.get_transcript(
            video_id=video_info["video_id"],
            channel_title=video_info["channel_title"],
            video_title=video_info["video_title"],
            save_subtitle=True,
        )
        if transcript:
            transcript.update(video_info)
            return transcript

        audio_file = self.download_audio(video_info["video_id"])
        if not audio_file:
            return {"error": "Failed to download audio", **video_info}

        return self.process_and_transcribe_audio(video_info, audio_file)

    def process_playlist(self, url: str) -> List[Dict[str, Any]]:
        """Process all videos in a YouTube playlist."""
        playlist_info = self.get_playlist_info(url)
        results = []

        for video_info in playlist_info:
            video_url = f"https://www.youtube.com/watch?v={video_info['video_id']}"
            result = self.process_single_video(video_url)
            results.append(result)

        return results

    def process_url(self, url: str) -> Any:
        """Processes a YouTube URL, whether it's a single video or a playlist.

        Args:
            url: The YouTube URL to process.

        Returns:
            If it's a playlist, returns the processed playlist information.
            If it's a single video, returns the processed video information.

        Raises:
            InvalidYoutubeVideoURL: If the provided URL is invalid.
        """
        playlist_id = self.extract_playlist_id(url)
        if playlist_id:
            return self.process_playlist(url)
        else:
            return self.process_single_video(url)


if __name__ == "__main__":
    analyzer = YoutubeAnalyzer(
        "stockllm/analyzer/youtube/config.json",
        url="https://www.youtube.com/watch?v=XuzK4YF69to",
    )
    print(analyzer.data)

# TODO:
# 1. Add a progress bar
# 2. Add a downloader
# 3. Add a transcriber
# 4. Add a summarizer
# 5. Add a saver
# 6. remove origin audio file
