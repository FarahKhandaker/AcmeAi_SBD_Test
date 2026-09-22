class PipelineError(Exception):
    """Base class for expected failures."""
    
class ConfigError(PipelineError):
    """config loading or validation fails."""
    
class DetectorError(PipelineError):
    """detector cannot be constructed or fatally fails."""
    
class ReporterError(PipelineError):
    """report is malformed."""