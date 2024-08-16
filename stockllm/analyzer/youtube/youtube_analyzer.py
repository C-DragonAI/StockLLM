from urllib.parse import parse_qs, urlparse

import whisper  # 假设您使用 OpenAI 的 Whisper 模型
import yt_dlp  # 用于下载 YouTube 音频
from youtube_transcript_api import YouTubeTranscriptApi

from stockllm.analyzer.base_analyzer import BaseAnalyzer


class InvalidYoutubeVideoURL(Exception):
    """Custom exception to represent an invalid YouTube video URL"""

    pass


class TranscriptNotAvailableError(Exception):
    """Custom exception to represent that the transcript for a YouTube video is not available"""

    pass


class YoutubeAnalyzer(BaseAnalyzer):
    def __init__(self, video_url) -> None:
        self.video_url = video_url
        self.video_id = self._get_video_id(video_url)
        super().__init__("")

    def load_configs(self, configs_file: str) -> dict:
        pass

    def _get_video_id(self, url):
        """Extract video ID from YouTube URL"""
        query = urlparse(url)
        if query.hostname == "youtu.be":
            return query.path[1:]
        if query.hostname in ("www.youtube.com", "youtube.com"):
            if query.path == "/watch":
                p = parse_qs(query.query)
                return p["v"][0]
            if query.path[:7] == "/embed/":
                return query.path.split("/")[2]
            if query.path[:3] == "/v/":
                return query.path.split("/")[2]
        return None

    def load_data(self):
        if not self.video_id:
            raise InvalidYoutubeVideoURL("Invalid YouTube URL")

        try:
            transcript = self._get_transcript_from_api()
        except TranscriptNotAvailableError:
            print("Transcript not available via API. Attempting to transcribe audio...")
            transcript = self._transcribe_audio()

        return transcript

    def _get_transcript_from_api(self):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                self.video_id, languages=["zh-TW"]
            )
            return transcript
        except Exception as e:
            raise TranscriptNotAvailableError(
                f"Could not retrieve transcript: {str(e)}"
            )

    def _transcribe_audio(self):
        audio_url = self._get_audio_url()
        audio_file = self._download_audio(audio_url)

        model = whisper.load_model("base")  # 加载 Whisper 模型
        result = model.transcribe(audio_file)

        # 将 Whisper 的输出格式转换为与 YouTubeTranscriptApi 相似的格式
        transcript = [
            {
                "text": segment["text"],
                "start": segment["start"],
                "duration": segment["end"] - segment["start"],
            }
            for segment in result["segments"]
        ]

        return transcript

    def _get_audio_url(self):
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "%(id)s.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.video_url, download=False)
            return info["url"]

    def _download_audio(self, audio_url):
        # 实现下载音频的逻辑
        # 返回下载的音频文件路径
        pass

    def analysis(self) -> str:
        pass


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=XuzK4YF69to"
    analyzer = YoutubeAnalyzer(video_url)
    if analyzer:
        print("Success")
    else:
        print("")
