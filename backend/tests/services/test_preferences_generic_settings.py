import json
import tempfile
from pathlib import Path

import pytest

from services.preferences_service import PreferencesService
from core.config import Settings


@pytest.fixture
def prefs_service(tmp_path: Path) -> PreferencesService:
    config_path = tmp_path / "config.json"
    settings = Settings()
    settings.config_file_path = config_path
    return PreferencesService(settings)


class TestGenericSettings:
    def test_get_setting_default_none(self, prefs_service: PreferencesService):
        assert prefs_service.get_setting("nonexistent") is None

    def test_save_and_get_setting(self, prefs_service: PreferencesService):
        prefs_service.save_setting("audiodb_sweep_cursor", "abc-123")
        assert prefs_service.get_setting("audiodb_sweep_cursor") == "abc-123"

    def test_save_none_removes_setting(self, prefs_service: PreferencesService):
        prefs_service.save_setting("audiodb_sweep_cursor", "abc-123")
        prefs_service.save_setting("audiodb_sweep_cursor", None)
        assert prefs_service.get_setting("audiodb_sweep_cursor") is None

    def test_settings_persist_across_instances(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        settings = Settings()
        settings.config_file_path = config_path

        svc1 = PreferencesService(settings)
        svc1.save_setting("cursor", "xyz")

        svc2 = PreferencesService(settings)
        assert svc2.get_setting("cursor") == "xyz"

    def test_internal_namespace_isolated(self, prefs_service: PreferencesService):
        prefs_service.save_setting("my_key", "my_val")
        config = prefs_service._load_config()
        assert "my_key" not in config
        assert config["_internal"]["my_key"] == "my_val"
