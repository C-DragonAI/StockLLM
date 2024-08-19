from unittest.mock import MagicMock, patch

import pytest

from stockllm.analyzer.youtube.youtube_analyzer import (
    InvalidYoutubeVideoURL,
    YoutubeAnalyzer,
)


@pytest.fixture
def analyzer():
    return YoutubeAnalyzer(
        "stockllm/analyzer/youtube/config.json",
        url="https://www.youtube.com/watch?v=XuzK4YF69to",
    )


def test_extract_video_id(analyzer):
    assert (
        analyzer.extract_video_id("https://www.youtube.com/watch?v=XuzK4YF69to")
        == "XuzK4YF69to"
    )
    assert analyzer.extract_video_id("https://youtu.be/XuzK4YF69to") == "XuzK4YF69to"
    assert (
        analyzer.extract_video_id("https://www.youtube.com/embed/XuzK4YF69to")
        == "XuzK4YF69to"
    )
    assert analyzer.extract_video_id("XuzK4YF69to") == "XuzK4YF69to"
    assert analyzer.extract_video_id("https://www.example.com") is None


def test_extract_playlist_id(analyzer):
    assert (
        analyzer.extract_playlist_id(
            "https://www.youtube.com/playlist?list=PLXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx"
        )
        == "PLXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx"
    )
    assert (
        analyzer.extract_playlist_id("https://www.youtube.com/watch?v=XuzK4YF69to")
        is None
    )


@patch("stockllm.analyzer.youtube.youtube_analyzer.yt_dlp.YoutubeDL")
def test_get_video_info(mock_YoutubeDL, analyzer):
    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {
        "id": "XuzK4YF69to",
        "title": "測試視頻",
        "channel": "測試頻道",
        "upload_date": "20230101",
        "view_count": 1000,
        "like_count": 100,
        "duration": 300,
        "description": "這是一個測試視頻",
        "tags": ["測試", "視頻"],
        "categories": ["教育"],
    }
    mock_YoutubeDL.return_value.__enter__.return_value = mock_ydl

    info = analyzer.get_video_info("https://www.youtube.com/watch?v=XuzK4YF69to")

    assert info["video_id"] == "XuzK4YF69to"
    assert info["video_title"] == "測試視頻"
    assert info["channel_title"] == "測試頻道"
    assert info["upload_date"] == "20230101"
    assert info["view_count"] == 1000
    assert info["like_count"] == 100
    assert info["duration"] == 300
    assert info["description"] == "這是一個測試視頻"
    assert info["tags"] == ["測試", "視頻"]
    assert info["categories"] == ["教育"]


@patch("stockllm.analyzer.youtube.youtube_analyzer.YouTubeTranscriptApi")
def test_get_transcript(mock_YouTubeTranscriptApi, analyzer):
    mock_YouTubeTranscriptApi.get_transcript.return_value = [
        {"text": "這是第一句話", "start": 0.0, "duration": 2.0},
        {"text": "這是第二句話", "start": 2.0, "duration": 2.0},
    ]
    analyzer.video_info = {
        "video_id": "XuzK4YF69to",
        "channel_title": "測試頻道",
        "video_title": "測試視頻",
    }

    transcript = analyzer.get_transcript(save_subtitle=False)

    assert transcript["channel_id"] == "測試頻道"
    assert transcript["video_title"] == "測試視頻"
    assert len(transcript["transcript"]) == 2
    assert transcript["transcript"][0]["text"] == "這是第一句話"


@patch("stockllm.analyzer.youtube.youtube_analyzer.yt_dlp.YoutubeDL")
def test_download_audio(mock_YoutubeDL, analyzer):
    mock_ydl = MagicMock()
    mock_YoutubeDL.return_value.__enter__.return_value = mock_ydl

    audio_file = analyzer.download_audio("XuzK4YF69to")

    assert audio_file == f"{analyzer.configs['output_dir']}/XuzK4YF69to.mp3"
    mock_ydl.download.assert_called_once_with(
        ["https://www.youtube.com/watch?v=XuzK4YF69to"]
    )


def test_process_url_single_video(analyzer):
    with patch.object(analyzer, "process_single_video") as mock_process_single_video:
        mock_process_single_video.return_value = {
            "video_id": "XuzK4YF69to",
            "title": "測試視頻",
        }
        result = analyzer.process_url("https://www.youtube.com/watch?v=XuzK4YF69to")
        assert result == {"video_id": "XuzK4YF69to", "title": "測試視頻"}
        mock_process_single_video.assert_called_once_with(
            "https://www.youtube.com/watch?v=XuzK4YF69to"
        )


def test_process_url_playlist(analyzer):
    with patch.object(analyzer, "process_playlist") as mock_process_playlist:
        mock_process_playlist.return_value = [
            {"video_id": "XuzK4YF69to", "title": "測試視頻"}
        ]
        result = analyzer.process_url(
            "https://www.youtube.com/playlist?list=PLXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx"
        )
        assert result == [{"video_id": "XuzK4YF69to", "title": "測試視頻"}]
        mock_process_playlist.assert_called_once_with(
            "https://www.youtube.com/playlist?list=PLXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx"
        )


def test_process_url_invalid(analyzer):
    with pytest.raises(InvalidYoutubeVideoURL):
        analyzer.process_url("https://www.example.com")
