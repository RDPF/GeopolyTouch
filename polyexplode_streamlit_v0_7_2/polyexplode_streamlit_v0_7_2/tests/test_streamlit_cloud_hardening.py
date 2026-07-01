from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_app_uses_current_streamlit_width_api() -> None:
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "use_container_width" not in app_text
    assert 'width="stretch"' in app_text


def test_app_exports_current_versioned_filenames() -> None:
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "v0_7_2" in app_text
    assert "v0_7_1" not in app_text


def test_streamlit_config_is_cloud_safe() -> None:
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'base = "dark"' in config
    assert "headless = true" in config
    assert "secrets" not in config.lower()


def test_requirements_raise_streamlit_floor_for_width_api() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "streamlit>=1.50" in requirements
