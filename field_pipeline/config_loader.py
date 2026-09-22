from pathlib import Path

import yaml
from pydantic import ValidationError

from field_pipeline.config import PipelineConfig
from field_pipeline.exceptions import ConfigError

def load_config(path: Path) -> PipelineConfig:
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")
    
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"Config file is not valid YAML: {path} ({exc})") from exc
    
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Config file must contain a mapping at the top level,"
            f"got {type(raw).__name__}"
        )
        
    try: 
        return PipelineConfig(**raw)
    except ValidationError as exc:
        raise ConfigError(f"Config file failed validation: {path}\n{exc}") from exc