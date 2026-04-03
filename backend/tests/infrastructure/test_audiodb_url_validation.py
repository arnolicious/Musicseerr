"""Tests for validate_audiodb_image_url SSRF protection."""
import pytest
from infrastructure.validators import validate_audiodb_image_url


class TestValidateAudiodbImageUrl:

    @pytest.mark.parametrize("url", [
        "https://www.theaudiodb.com/images/media/thumb.jpg",
        "https://theaudiodb.com/images/media/artist/thumb/coldplay.jpg",
        "https://r2.theaudiodb.com/images/album/thumb/parachutes.jpg",
        "https://r2.theaudiodb.com/images/artist/fanart/coldplay1.jpg",
    ])
    def test_valid_audiodb_urls(self, url: str) -> None:
        assert validate_audiodb_image_url(url) is True

    @pytest.mark.parametrize("url", [
        "http://www.theaudiodb.com/images/media/thumb.jpg",
        "http://r2.theaudiodb.com/images/album/thumb.jpg",
    ])
    def test_rejects_http_scheme(self, url: str) -> None:
        assert validate_audiodb_image_url(url) is False

    @pytest.mark.parametrize("url", [
        "ftp://r2.theaudiodb.com/file.jpg",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
        "javascript:alert(1)",
    ])
    def test_rejects_non_https_schemes(self, url: str) -> None:
        assert validate_audiodb_image_url(url) is False

    @pytest.mark.parametrize("url", [
        "https://evil.com/images/media/thumb.jpg",
        "https://theaudiodb.com.evil.com/exploit.jpg",
        "https://attacker.theaudiodb.com/images/thumb.jpg",
        "https://notaudiodb.com/images/thumb.jpg",
        "https://example.com/redirect?url=https://r2.theaudiodb.com/img.jpg",
    ])
    def test_rejects_unknown_hosts(self, url: str) -> None:
        assert validate_audiodb_image_url(url) is False

    @pytest.mark.parametrize("url", [
        "https://127.0.0.1/images/thumb.jpg",
        "https://10.0.0.1/images/thumb.jpg",
        "https://192.168.1.1/images/thumb.jpg",
        "https://[::1]/images/thumb.jpg",
        "https://169.254.169.254/latest/meta-data/",
    ])
    def test_rejects_private_and_loopback_ips(self, url: str) -> None:
        assert validate_audiodb_image_url(url) is False

    @pytest.mark.parametrize("url", [
        "",
        None,
        "   ",
        "not-a-url",
        "://missing-scheme.com",
    ])
    def test_rejects_invalid_inputs(self, url) -> None:
        assert validate_audiodb_image_url(url) is False

    def test_rejects_url_without_host(self) -> None:
        assert validate_audiodb_image_url("https:///path/only") is False
