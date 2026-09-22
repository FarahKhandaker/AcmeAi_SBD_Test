from pathlib import Path

import pytest

from field_pipeline.config_loader import load_config
from field_pipeline.exceptions import ConfigError

def _write(tmp_path: Path, name: str, contents: str) -> Path:
    p = tmp_path / name
    p.write_text(contents)
    return p

def test_missing_files(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yaml")

def test_malformed_yaml(tmp_path):
    p = _write(tmp_path, "bad.yaml", "key: [unclosed")
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_config(p)


def test_non_mapping_top_level(tmp_path):
    p = _write(tmp_path, "list.yaml", "- one\n- two\n")
    with pytest.raises(ConfigError, match="mapping at the top level"):
        load_config(p)


def test_schema_violation(tmp_path):
    p = _write(
        tmp_path,
        "bad_schema.yaml",
        "video_path: x.mp4\ntarget_fps: -5\nfield_detector:\n"
        "  type: mask_color_v1\n  sport: football\n  min_area: 100\n",
    )
    with pytest.raises(ConfigError, match="failed validation"):
        load_config(p)


def test_valid_yaml_returns_config(tmp_path):
    p = _write(
        tmp_path,
        "ok.yaml",
        "video_path: x.mp4\ntarget_fps: 30\nfield_detector:\n"
        "  type: mask_color_v1\n  sport: football\n  min_area: 100\n",
    )
    config = load_config(p)
    assert config.target_fps == 30