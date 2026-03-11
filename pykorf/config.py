"""Configuration management for pyKorf.

Provides a centralized configuration system with support for:
- Environment variables
- Configuration files (JSON, YAML, TOML)
- Runtime overrides
- Type-safe access

Example:
    >>> from pykorf.config import get_config, Config
    >>> config = get_config()
    >>> print(config.io.default_encoding)
    >>> # Override at runtime
    >>> config.io.default_encoding = "utf-8"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import tomli_w  # noqa: F401


@dataclass
class IOConfig:
    """I/O-related configuration."""

    default_encoding: str = "latin-1"
    newline: str = "\r\n"
    backup_files: bool = True
    backup_suffix: str = ".bak"
    max_file_size_mb: int = 100

    def __post_init__(self) -> None:
        # Allow override from environment
        if env_encoding := os.getenv("PYKORF_ENCODING"):
            self.default_encoding = env_encoding


@dataclass
class ValidationConfig:
    """Validation-related configuration."""

    strict_mode: bool = False
    check_connectivity_on_save: bool = True
    check_layout_on_save: bool = False
    allow_unknown_parameters: bool = True
    max_name_length: int = 9
    warn_on_calculated_overwrite: bool = True

    def __post_init__(self) -> None:
        if env_strict := os.getenv("PYKORF_STRICT_VALIDATION"):
            self.strict_mode = env_strict.lower() in ("1", "true", "yes")


@dataclass
class PerformanceConfig:
    """Performance-related configuration."""

    cache_size: int = 128
    enable_caching: bool = True
    lazy_loading: bool = True
    max_elements_for_auto_layout: int = 1000

    def __post_init__(self) -> None:
        if env_cache := os.getenv("PYKORF_CACHE_SIZE"):
            self.cache_size = int(env_cache)


@dataclass
class LoggingConfig:
    """Logging-related configuration."""

    level: str = "INFO"
    format: str = "structured"  # "structured" or "console"
    show_file_path: bool = False
    show_line_numbers: bool = False

    def __post_init__(self) -> None:
        if env_level := os.getenv("PYKORF_LOG_LEVEL"):
            self.level = env_level.upper()


@dataclass
class ExportConfig:
    """Export-related configuration."""

    default_format: str = "json"
    include_metadata: bool = True
    include_results: bool = True
    pretty_print: bool = True
    float_precision: int = 6


@dataclass
class Config:
    """Main configuration class for pyKorf.

    Attributes:
        io: I/O configuration
        validation: Validation configuration
        performance: Performance configuration
        logging: Logging configuration
        export: Export configuration
    """

    io: IOConfig = field(default_factory=IOConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create configuration from a dictionary."""
        io = IOConfig(**data.get("io", {}))
        validation = ValidationConfig(**data.get("validation", {}))
        performance = PerformanceConfig(**data.get("performance", {}))
        logging = LoggingConfig(**data.get("logging", {}))
        export = ExportConfig(**data.get("export", {}))

        return cls(
            io=io,
            validation=validation,
            performance=performance,
            logging=logging,
            export=export,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> Config:
        """Load configuration from a file.

        Supports JSON, YAML, and TOML formats.
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8")

        if path.suffix == ".json":
            import json

            data = json.loads(content)
        elif path.suffix in (".yaml", ".yml"):
            import yaml

            data = yaml.safe_load(content)
        elif path.suffix == ".toml":
            import tomllib

            data = tomllib.loads(content)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""
        result: dict[str, Any] = {}
        for f in fields(self):
            section = getattr(self, f.name)
            result[f.name] = {field.name: getattr(section, field.name) for field in fields(section)}
        return result

    def save(self, path: str | Path) -> None:
        """Save configuration to a file."""
        path = Path(path)
        data = self.to_dict()

        if path.suffix == ".json":
            import json

            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        elif path.suffix in (".yaml", ".yml"):
            import yaml

            path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
        elif path.suffix == ".toml":
            import tomli_w

            path.write_bytes(tomli_w.dumps(data))
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Creates a default configuration if none exists.
    """
    global _config
    if _config is None:
        _config = Config()

        # Try to load from standard locations
        config_paths = [
            Path("pykorf.toml"),
            Path("pykorf.yaml"),
            Path("pykorf.json"),
            Path.home() / ".config" / "pykorf" / "config.toml",
            Path.home() / ".pykorf.toml",
        ]

        for path in config_paths:
            if path.exists():
                try:
                    _config = Config.from_file(path)
                    break
                except Exception:
                    continue

    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config
    _config = Config()


__all__ = [
    "Config",
    "ExportConfig",
    "IOConfig",
    "LoggingConfig",
    "PerformanceConfig",
    "ValidationConfig",
    "get_config",
    "reset_config",
    "set_config",
]
