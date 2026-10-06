"""Unit tests for SmartRouter — pure logic, no Qt/network required.

Run with:  pytest tests/test_router.py
"""
from grabit.core.router import SmartRouter, _classify_direct_extension


def _status(**overrides):
    base = {"streamlink": False, "spotdl": False, "aria2c": False, "playwright": False}
    base.update(overrides)
    return base


def test_youtube_routes_to_ytdlp():
    decision = SmartRouter.route("https://www.youtube.com/watch?v=abc123", _status())
    assert decision.engine == "yt-dlp"
    assert decision.is_known


def test_instagram_routes_to_instaloader():
    decision = SmartRouter.route("https://www.instagram.com/p/XYZ/", _status())
    assert decision.engine == "instaloader"


def test_twitch_video_uses_twitch_engine_even_with_streamlink():
    decision = SmartRouter.route("https://www.twitch.tv/videos/12345", _status(streamlink=True))
    assert decision.engine == "twitch"


def test_twitch_live_prefers_streamlink_when_available():
    decision = SmartRouter.route("https://www.twitch.tv/somechannel", _status(streamlink=True))
    assert decision.engine == "streamlink"


def test_twitch_live_falls_back_to_twitch_engine_without_streamlink():
    decision = SmartRouter.route("https://www.twitch.tv/somechannel", _status(streamlink=False))
    assert decision.engine == "twitch"


def test_magnet_link_uses_aria2_when_available():
    magnet = "magnet:?xt=urn:btih:abcdef0123456789abcdef0123456789abcdef01"
    decision = SmartRouter.route(magnet, _status(aria2c=True))
    assert decision.engine == "aria2"


def test_magnet_link_without_aria2_is_unknown():
    magnet = "magnet:?xt=urn:btih:abcdef0123456789abcdef0123456789abcdef01"
    decision = SmartRouter.route(magnet, _status(aria2c=False))
    assert decision.engine is None


def test_direct_video_extension_is_classified_correctly():
    decision = SmartRouter.route("https://example.com/clip.mp4", _status())
    assert decision.kind == "video"
    assert decision.engine == "direct"


def test_direct_audio_extension_is_classified_correctly():
    # Regression test: the original script's slice-based classification
    # mislabeled every audio extension as "image".
    assert _classify_direct_extension(".mp3") == "audio"
    assert _classify_direct_extension(".flac") == "audio"


def test_direct_image_extension_is_classified_correctly():
    # Regression test: the original slice put .bmp/.svg/.tiff/.tif/.ico/
    # .heic/.avif (and .zip!) into "audio" instead of "image"/"file".
    assert _classify_direct_extension(".bmp") == "image"
    assert _classify_direct_extension(".avif") == "image"
    assert _classify_direct_extension(".zip") == "file"


def test_rclone_pseudo_scheme():
    decision = SmartRouter.route("rclone://myremote/path/to/file", _status())
    assert decision.engine == "rclone"


def test_unknown_scheme_is_unknown():
    decision = SmartRouter.route("not a url at all", _status())
    assert decision.engine is None
