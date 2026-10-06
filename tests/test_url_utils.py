from grabit.core.url_utils import extract_urls_regex, is_valid_url


def test_is_valid_url_accepts_http():
    assert is_valid_url("https://example.com/video.mp4")


def test_is_valid_url_rejects_plain_text():
    assert not is_valid_url("just some text")


def test_is_valid_url_accepts_magnet_with_btih():
    assert is_valid_url("magnet:?xt=urn:btih:abcdef0123456789abcdef0123456789abcdef01")


def test_is_valid_url_rejects_magnet_without_btih():
    assert not is_valid_url("magnet:?dn=somefile")


def test_is_valid_url_accepts_rclone_scheme():
    assert is_valid_url("rclone://remote/path")


def test_extract_urls_regex_finds_multiple_urls():
    text = "check https://a.com/1.mp4 and also https://b.com/2.mp4!"
    urls = extract_urls_regex(text)
    assert urls == ["https://a.com/1.mp4", "https://b.com/2.mp4"]


def test_extract_urls_regex_strips_trailing_punctuation():
    text = "see (https://example.com/page)."
    urls = extract_urls_regex(text)
    assert urls == ["https://example.com/page"]
