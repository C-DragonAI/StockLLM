from unittest.mock import MagicMock, patch

import pytest

from stockllm.analyzer.youtube.youtube_analyzer import YoutubeAnalyzer


@pytest.fixture
def analyzer():
    return YoutubeAnalyzer("dummy_video_id")


def test_get_video_id_youtu_be(analyzer):
    url = "https://youtu.be/XuzK4YF69to"
    assert analyzer._get_video_id(url) == "XuzK4YF69to"


def test_get_video_id_youtube_com(analyzer):
    url = "https://www.youtube.com/watch?v=XuzK4YF69to"
    assert analyzer._get_video_id(url) == "XuzK4YF69to"


def test_get_video_id_embed(analyzer):
    url = "https://www.youtube.com/embed/XuzK4YF69to"
    assert analyzer._get_video_id(url) == "XuzK4YF69to"


def test_get_video_id_invalid(analyzer):
    url = "https://www.example.com/watch?v=XuzK4YF69to"
    assert analyzer._get_video_id(url) is None


def test_load_data():
    video_url = "https://www.youtube.com/watch?v=XuzK4YF69to"
    analyzer = YoutubeAnalyzer(video_url)

    with patch(
        "stockllm.analyzer.youtube.youtube_analyzer.YouTubeTranscriptApi.list_transcripts"
    ) as mock_list_transcripts:
        mock_transcript = MagicMock()
        mock_transcript.find_transcript.return_value.fetch.return_value = [
            {"text": "測試字幕1"},
            {"text": "測試字幕2"},
        ]
        mock_list_transcripts.return_value = mock_transcript

        with patch("builtins.print") as mock_print:
            analyzer.load_data()
            mock_list_transcripts.assert_called_once_with("dQw4w9WgXcQ")
            mock_transcript.find_transcript.assert_called_once_with(["zh-Hant"])
            mock_print.assert_any_call(mock_transcript)


def test_get_transcript_from_api(analyzer):
    with patch(
        "stockllm.analyzer.youtube.youtube_analyzer.YouTubeTranscriptApi.get_transcript"
    ) as mock_get_transcript:
        mock_get_transcript.return_value = [{"text": "测试字幕1"}, {"text": "测试字幕2"}]
        transcript = analyzer._get_transcript_from_api()
        mock_get_transcript.assert_called_once_with(
            analyzer.video_id, languages=["zh-TW"]
        )
        assert transcript == [{"text": "测试字幕1"}, {"text": "测试字幕2"}]


def test_get_transcript_from_api_error(analyzer):
    with patch(
        "stockllm.analyzer.youtube.youtube_analyzer.YouTubeTranscriptApi.get_transcript"
    ) as mock_get_transcript:
        mock_get_transcript.side_effect = Exception("API错误")
        with pytest.raises(analyzer.TranscriptNotAvailableError):
            analyzer._get_transcript_from_api()


@patch("stockllm.analyzer.youtube.youtube_analyzer.whisper.load_model")
@patch("stockllm.analyzer.youtube.youtube_analyzer.YoutubeAnalyzer._get_audio_url")
@patch("stockllm.analyzer.youtube.youtube_analyzer.YoutubeAnalyzer._download_audio")
def test_transcribe_audio(
    mock_download_audio, mock_get_audio_url, mock_load_model, analyzer
):
    mock_get_audio_url.return_value = "fake_audio_url"
    mock_download_audio.return_value = "fake_audio_file.mp3"
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"text": "测试文本1", "start": 0, "end": 2},
            {"text": "测试文本2", "start": 2, "end": 4},
        ]
    }
    mock_load_model.return_value = mock_model

    transcript = analyzer._transcribe_audio()

    mock_get_audio_url.assert_called_once()
    mock_download_audio.assert_called_once_with("fake_audio_url")
    mock_load_model.assert_called_once_with("base")
    mock_model.transcribe.assert_called_once_with("fake_audio_file.mp3")

    expected_transcript = [
        {"text": "测试文本1", "start": 0, "duration": 2},
        {"text": "测试文本2", "start": 2, "duration": 2},
    ]
    assert transcript == expected_transcript


@patch("stockllm.analyzer.youtube.youtube_analyzer.yt_dlp.YoutubeDL")
def test_get_audio_url(mock_YoutubeDL, analyzer):
    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = {"url": "fake_audio_url"}
    mock_YoutubeDL.return_value.__enter__.return_value = mock_ydl

    audio_url = analyzer._get_audio_url()

    assert audio_url == "fake_audio_url"
    mock_ydl.extract_info.assert_called_once_with(analyzer.video_url, download=False)
