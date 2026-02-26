"""
Configuration management module.
Loads and validates configuration from config.ini.
"""

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Typed configuration container."""
    # Invoca credentials
    invoca_email: str
    invoca_password: str
    invoca_oauth_token: str
    invoca_network_id: str

    # Browser settings
    headless: bool
    timeout: int

    # OpenAI (Whisper only)
    openai_api_key: str

    # OpenRouter (LLM tasks)
    openrouter_api_key: str
    openrouter_model: str

    # Paths
    recordings_dir: Path
    transcripts_dir: Path
    prompts_dir: Path

    @property
    def base_dir(self) -> Path:
        """Return the base project directory."""
        return self.recordings_dir.parent


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from ini file.

    Args:
        config_path: Path to config.ini. If None, uses config.ini in script directory.

    Returns:
        Config dataclass with all settings.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If required fields are missing or invalid.
    """
    if config_path is None:
        config_file = Path(__file__).parent.parent / "config.ini"
    else:
        config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    parser = configparser.ConfigParser()
    parser.read(config_file)

    base_dir = config_file.parent

    # Validate required sections
    required_sections = ["invoca", "openai", "openrouter"]
    for section in required_sections:
        if section not in parser:
            raise ValueError(f"Missing required section [{section}] in config.ini")

    # Build config object
    config = Config(
        # Invoca
        invoca_email=parser.get("invoca", "email"),
        invoca_password=parser.get("invoca", "password"),
        invoca_oauth_token=parser.get("invoca", "oauth_token"),
        invoca_network_id=parser.get("invoca", "network_id", fallback="1595"),

        # Browser settings
        headless=parser.getboolean("settings", "headless", fallback=False),
        timeout=parser.getint("settings", "timeout", fallback=30000),

        # OpenAI
        openai_api_key=parser.get("openai", "api_key"),

        # OpenRouter
        openrouter_api_key=parser.get("openrouter", "api_key"),
        openrouter_model=parser.get("openrouter", "model", fallback="x-ai/grok-3-fast"),

        # Paths
        recordings_dir=base_dir / parser.get("paths", "recordings_dir", fallback="recordings"),
        transcripts_dir=base_dir / parser.get("paths", "transcripts_dir", fallback="transcripts"),
        prompts_dir=base_dir / parser.get("paths", "prompts_dir", fallback="prompts"),
    )

    # Validate credentials
    _validate_config(config)

    return config


def _validate_config(config: Config) -> None:
    """Validate that credentials are properly set."""
    placeholders = ["YOUR_", "xxx", "placeholder"]

    def is_placeholder(value: str) -> bool:
        return any(p in value.upper() for p in [p.upper() for p in placeholders])

    if is_placeholder(config.invoca_email):
        raise ValueError("Please set your Invoca email in config.ini")

    if is_placeholder(config.invoca_password):
        raise ValueError("Please set your Invoca password in config.ini")

    if is_placeholder(config.openai_api_key):
        raise ValueError("Please set your OpenAI API key in config.ini")

    if is_placeholder(config.openrouter_api_key):
        raise ValueError("Please set your OpenRouter API key in config.ini")
