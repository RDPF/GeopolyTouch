from __future__ import annotations

from pathlib import Path

import polyexplode

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_cloud_hardening_release() -> None:
    assert polyexplode.__version__ == "0.7.2"


def test_cloud_repository_files_exist() -> None:
    required = [
        "app.py",
        "requirements.txt",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        ".gitignore",
        ".python-version",
        ".streamlit/config.toml",
        ".github/workflows/tests.yml",
        "docs/STREAMLIT_CLOUD_DEPLOY.md",
        "docs/RELEASE_CHECKLIST.md",
        "examples/tetrahedron.json",
        "examples/cube.off",
        "catalog_summary_streamlit_v0_7_2.csv",
        "catalog_summary_streamlit_v0_7_2.json",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert missing == []


def test_requirements_include_streamlit_plotly_numpy_pytest() -> None:
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    for package in ["streamlit", "plotly", "numpy", "pytest"]:
        assert package in text.lower()


def test_only_current_catalog_summary_is_kept_at_repository_root() -> None:
    summaries = sorted(path.name for path in ROOT.glob("catalog_summary_streamlit_v*.csv"))
    assert summaries == ["catalog_summary_streamlit_v0_7_2.csv"]
