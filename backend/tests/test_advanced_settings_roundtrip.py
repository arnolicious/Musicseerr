"""Round-trip tests for AdvancedSettings ↔ AdvancedSettingsFrontend conversion."""

import msgspec
import pytest

from api.v1.schemas.advanced_settings import AdvancedSettings, AdvancedSettingsFrontend


class TestDirectRemoteImagesRoundTrip:
    def test_default_value_is_true(self) -> None:
        settings = AdvancedSettings()
        assert settings.direct_remote_images_enabled is True

    def test_frontend_default_is_true(self) -> None:
        frontend = AdvancedSettingsFrontend()
        assert frontend.direct_remote_images_enabled is True

    def test_roundtrip_preserves_true(self) -> None:
        backend = AdvancedSettings(direct_remote_images_enabled=True)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.direct_remote_images_enabled is True
        restored = frontend.to_backend()
        assert restored.direct_remote_images_enabled is True

    def test_roundtrip_preserves_false(self) -> None:
        backend = AdvancedSettings(direct_remote_images_enabled=False)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.direct_remote_images_enabled is False
        restored = frontend.to_backend()
        assert restored.direct_remote_images_enabled is False


class TestAudioDBNameSearchFallbackRoundTrip:
    def test_default_value_is_false(self) -> None:
        settings = AdvancedSettings()
        assert settings.audiodb_name_search_fallback is False

    def test_frontend_default_is_false(self) -> None:
        frontend = AdvancedSettingsFrontend()
        assert frontend.audiodb_name_search_fallback is False

    def test_roundtrip_preserves_true(self) -> None:
        backend = AdvancedSettings(audiodb_name_search_fallback=True)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.audiodb_name_search_fallback is True
        restored = frontend.to_backend()
        assert restored.audiodb_name_search_fallback is True

    def test_roundtrip_preserves_false(self) -> None:
        backend = AdvancedSettings(audiodb_name_search_fallback=False)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.audiodb_name_search_fallback is False
        restored = frontend.to_backend()
        assert restored.audiodb_name_search_fallback is False


class TestCacheTtlAudiodbFoundRoundTrip:
    def test_default_value(self) -> None:
        settings = AdvancedSettings()
        frontend = AdvancedSettingsFrontend.from_backend(settings)
        assert frontend.cache_ttl_audiodb_found == 168

    def test_roundtrip_preserves(self) -> None:
        backend = AdvancedSettings(cache_ttl_audiodb_found=604800)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.cache_ttl_audiodb_found == 168
        restored = frontend.to_backend()
        assert restored.cache_ttl_audiodb_found == 604800

    def test_custom_value_roundtrip(self) -> None:
        backend = AdvancedSettings(cache_ttl_audiodb_found=36000)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.cache_ttl_audiodb_found == 10
        restored = frontend.to_backend()
        assert restored.cache_ttl_audiodb_found == 36000


class TestCacheTtlAudiodbNotFoundRoundTrip:
    def test_default_value(self) -> None:
        settings = AdvancedSettings()
        frontend = AdvancedSettingsFrontend.from_backend(settings)
        assert frontend.cache_ttl_audiodb_not_found == 24

    def test_roundtrip_preserves(self) -> None:
        backend = AdvancedSettings(cache_ttl_audiodb_not_found=86400)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.cache_ttl_audiodb_not_found == 24
        restored = frontend.to_backend()
        assert restored.cache_ttl_audiodb_not_found == 86400

    def test_custom_value_roundtrip(self) -> None:
        backend = AdvancedSettings(cache_ttl_audiodb_not_found=7200)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.cache_ttl_audiodb_not_found == 2
        restored = frontend.to_backend()
        assert restored.cache_ttl_audiodb_not_found == 7200


class TestCacheTtlAudiodbLibraryRoundTrip:
    def test_default_value(self) -> None:
        settings = AdvancedSettings()
        frontend = AdvancedSettingsFrontend.from_backend(settings)
        assert frontend.cache_ttl_audiodb_library == 336

    def test_roundtrip_preserves(self) -> None:
        backend = AdvancedSettings(cache_ttl_audiodb_library=1209600)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.cache_ttl_audiodb_library == 336
        restored = frontend.to_backend()
        assert restored.cache_ttl_audiodb_library == 1209600


class TestCacheTtlRecentlyViewedBytesRoundTrip:
    def test_default_value(self) -> None:
        settings = AdvancedSettings()
        frontend = AdvancedSettingsFrontend.from_backend(settings)
        assert frontend.cache_ttl_recently_viewed_bytes == 48

    def test_roundtrip_preserves(self) -> None:
        backend = AdvancedSettings(cache_ttl_recently_viewed_bytes=172800)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.cache_ttl_recently_viewed_bytes == 48
        restored = frontend.to_backend()
        assert restored.cache_ttl_recently_viewed_bytes == 172800


class TestAudiodbValidationClamping:
    def test_cache_ttl_found_below_min(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_audiodb_found=100)

    def test_cache_ttl_found_above_max(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_audiodb_found=99999999)

    def test_cache_ttl_not_found_below_min(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_audiodb_not_found=100)

    def test_cache_ttl_not_found_above_max(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_audiodb_not_found=999999)

    def test_cache_ttl_library_below_min(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_audiodb_library=100)

    def test_cache_ttl_library_above_max(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_audiodb_library=99999999)

    def test_cache_ttl_recently_viewed_bytes_below_min(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_recently_viewed_bytes=100)

    def test_cache_ttl_recently_viewed_bytes_above_max(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            AdvancedSettings(cache_ttl_recently_viewed_bytes=999999)

    def test_api_key_empty_coerced(self) -> None:
        settings = AdvancedSettings(audiodb_api_key="")
        assert settings.audiodb_api_key == "123"

    def test_api_key_whitespace_coerced(self) -> None:
        settings = AdvancedSettings(audiodb_api_key="   ")
        assert settings.audiodb_api_key == "123"


class TestAudiodbEnabledRoundTrip:
    def test_default_is_true(self) -> None:
        settings = AdvancedSettings()
        frontend = AdvancedSettingsFrontend.from_backend(settings)
        assert frontend.audiodb_enabled is True

    def test_roundtrip_false(self) -> None:
        backend = AdvancedSettings(audiodb_enabled=False)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.audiodb_enabled is False
        restored = frontend.to_backend()
        assert restored.audiodb_enabled is False

    def test_roundtrip_true(self) -> None:
        backend = AdvancedSettings(audiodb_enabled=True)
        frontend = AdvancedSettingsFrontend.from_backend(backend)
        assert frontend.audiodb_enabled is True
        restored = frontend.to_backend()
        assert restored.audiodb_enabled is True
