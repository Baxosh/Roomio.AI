"""
Configuration module for Vanna AI application.
Manages environment variables and application settings.
"""

import os
from dataclasses import dataclass
from typing import Final, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for default values
DEFAULT_POSTGRES_HOST: Final[str] = "localhost"
DEFAULT_POSTGRES_PORT: Final[int] = 5432
DEFAULT_POSTGRES_DB: Final[str] = "postgres"
DEFAULT_POSTGRES_USER: Final[str] = "postgres"
DEFAULT_POSTGRES_PASSWORD: Final[str] = "postgres"

DEFAULT_LLM_MODEL: Final[str] = "deepseek-chat"
DEFAULT_LLM_BASE_URL: Final[str] = "https://api.deepseek.com/v1"
DEFAULT_LLM_TEMPERATURE: Final[float] = 0.7

DEFAULT_AGENT_MAX_ITERATIONS: Final[int] = 50
DEFAULT_SCHEMA_FILE: Final[str] = "structure.txt"
DEFAULT_CHROMA_DB_PATH: Final[str] = "./chroma_db"
DEFAULT_APP_PORT: Final[int] = 8000

DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_LOG_FILE: Final[str] = "logs/vanna_app.log"
MB_TO_BYTES: Final[int] = 1024 * 1024
DEFAULT_LOG_MAX_MB: Final[int] = 10
DEFAULT_LOG_BACKUP_COUNT: Final[int] = 5

DEFAULT_FASTAPI_TITLE: Final[str] = "Vanna AI - SQL Query Assistant"
DEFAULT_FASTAPI_VERSION: Final[str] = "0.1.0"
DEFAULT_FASTAPI_DESCRIPTION: Final[str] = (
    "Multi-tenant SQL query assistant powered by Vanna AI and DeepSeek"
)

DEFAULT_CORS_METHODS: Final[str] = "GET,POST,PUT,DELETE,OPTIONS,PATCH"


# Helper functions for environment variable parsing
def _parse_bool_env(key: str, default: bool = False) -> bool:
    """Parse boolean environment variable.

    Accepts: true/false, yes/no, 1/0, on/off (case-insensitive)

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Boolean value
    """
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "yes", "1", "on")


def _parse_csv_env(key: str, default: str) -> list[str]:
    """Parse comma-separated environment variable into list.

    Args:
        key: Environment variable name
        default: Default comma-separated string

    Returns:
        List of stripped strings
    """
    value = os.getenv(key, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_int_env(key: str, default: int) -> int:
    """Parse integer environment variable.

    Args:
        key: Environment variable name
        default: Default integer value

    Returns:
        Integer value
    """
    value = os.getenv(key, str(default))
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float_env(key: str, default: float) -> float:
    """Parse float environment variable.

    Args:
        key: Environment variable name
        default: Default float value

    Returns:
        Float value
    """
    value = os.getenv(key, str(default))
    try:
        return float(value)
    except ValueError:
        return default


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database configuration from environment variables."""
        return cls(
            host=os.getenv("POSTGRES_HOST", DEFAULT_POSTGRES_HOST),
            port=_parse_int_env("POSTGRES_PORT", DEFAULT_POSTGRES_PORT),
            database=os.getenv("POSTGRES_DB", DEFAULT_POSTGRES_DB),
            user=os.getenv("POSTGRES_USER", DEFAULT_POSTGRES_USER),
            password=os.getenv("POSTGRES_PASSWORD", DEFAULT_POSTGRES_PASSWORD),
        )

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def __repr__(self) -> str:
        """Safe representation without exposing password."""
        return (
            f"DatabaseConfig(host={self.host}, port={self.port}, "
            f"database={self.database}, user={self.user}, password=***)"
        )


@dataclass
class LLMConfig:
    """LLM service configuration."""

    model: str
    api_key: str
    base_url: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load LLM configuration from environment variables."""
        max_tokens_str = os.getenv("LLM_MAX_TOKENS", "").strip()
        max_tokens = int(max_tokens_str) if max_tokens_str else None

        return cls(
            model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
            temperature=_parse_float_env("LLM_TEMPERATURE", DEFAULT_LLM_TEMPERATURE),
            max_tokens=max_tokens,
        )

    def __repr__(self) -> str:
        """Safe representation without exposing API key."""
        return (
            f"LLMConfig(model={self.model}, base_url={self.base_url}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens}, api_key=***)"
        )


@dataclass
class AgentConfig:
    """Agent behavior configuration."""

    max_tool_iterations: int
    stream_responses: bool
    auto_save_conversations: bool
    include_thinking_indicators: bool

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load agent configuration from environment variables."""
        return cls(
            max_tool_iterations=_parse_int_env(
                "AGENT_MAX_ITERATIONS", DEFAULT_AGENT_MAX_ITERATIONS
            ),
            stream_responses=_parse_bool_env("AGENT_STREAM_RESPONSES", True),
            auto_save_conversations=_parse_bool_env(
                "AGENT_AUTO_SAVE_CONVERSATIONS", True
            ),
            include_thinking_indicators=_parse_bool_env(
                "AGENT_THINKING_INDICATORS", True
            ),
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str
    file: str
    max_bytes: int
    backup_count: int

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load logging configuration from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            file=os.getenv("LOG_FILE", DEFAULT_LOG_FILE),
            max_bytes=_parse_int_env(
                "LOG_MAX_BYTES", DEFAULT_LOG_MAX_MB * MB_TO_BYTES
            ),
            backup_count=_parse_int_env("LOG_BACKUP_COUNT", DEFAULT_LOG_BACKUP_COUNT),
        )


@dataclass
class FastAPIConfig:
    """FastAPI and CORS configuration."""

    # FastAPI metadata
    title: str
    version: str
    description: str
    dev_mode: bool
    static_folder: Optional[str]

    # CORS configuration
    cors_enabled: bool
    cors_allow_origins: list[str]
    cors_allow_credentials: bool
    cors_allow_methods: list[str]
    cors_allow_headers: list[str]

    @classmethod
    def from_env(cls) -> "FastAPIConfig":
        """Load FastAPI configuration from environment variables."""
        return cls(
            # FastAPI metadata
            title=os.getenv("FASTAPI_TITLE", DEFAULT_FASTAPI_TITLE),
            version=os.getenv("FASTAPI_VERSION", DEFAULT_FASTAPI_VERSION),
            description=os.getenv("FASTAPI_DESCRIPTION", DEFAULT_FASTAPI_DESCRIPTION),
            dev_mode=_parse_bool_env("FASTAPI_DEV_MODE", False),
            static_folder=os.getenv("FASTAPI_STATIC_FOLDER") or None,
            # CORS configuration
            cors_enabled=_parse_bool_env("CORS_ENABLED", True),
            cors_allow_origins=_parse_csv_env("CORS_ALLOW_ORIGINS", "*"),
            cors_allow_credentials=_parse_bool_env("CORS_ALLOW_CREDENTIALS", True),
            cors_allow_methods=_parse_csv_env("CORS_ALLOW_METHODS", DEFAULT_CORS_METHODS),
            cors_allow_headers=_parse_csv_env("CORS_ALLOW_HEADERS", "*"),
        )

    def to_dict(self) -> dict:
        """
        Convert FastAPIConfig to dictionary format expected by VannaFastAPIServer.

        Returns:
            Dictionary with FastAPI and CORS configuration for VannaFastAPIServer.
        """
        config_dict = {
            # FastAPI settings at top level
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "dev_mode": self.dev_mode,
            # CORS settings nested under 'cors'
            "cors": {
                "enabled": self.cors_enabled,
                "allow_origins": self.cors_allow_origins,
                "allow_credentials": self.cors_allow_credentials,
                "allow_methods": self.cors_allow_methods,
                "allow_headers": self.cors_allow_headers,
            },
        }

        # Only include static_folder if it's set
        if self.static_folder:
            config_dict["static_folder"] = self.static_folder

        return config_dict


@dataclass
class AppConfig:
    """Main application configuration."""

    database: DatabaseConfig
    llm: LLMConfig
    agent: AgentConfig
    logging: LoggingConfig
    fastapi: FastAPIConfig
    schema_file: str
    chroma_db_path: str
    app_port: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load complete application configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            llm=LLMConfig.from_env(),
            agent=AgentConfig.from_env(),
            fastapi=FastAPIConfig.from_env(),
            logging=LoggingConfig.from_env(),
            schema_file=os.getenv("SCHEMA_FILE", DEFAULT_SCHEMA_FILE),
            chroma_db_path=os.getenv("CHROMA_DB_PATH", DEFAULT_CHROMA_DB_PATH),
            app_port=_parse_int_env("APP_PORT", DEFAULT_APP_PORT),
        )

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []

        # Validate required fields
        if not self.llm.api_key:
            errors.append("DEEPSEEK_API_KEY is required but not set")

        if not self.database.password:
            errors.append("POSTGRES_PASSWORD is required but not set")

        if not self.database.database:
            errors.append("POSTGRES_DB is required but not set")

        # Validate ranges
        if self.agent.max_tool_iterations < 1:
            errors.append("AGENT_MAX_ITERATIONS must be at least 1")

        if not (0.0 <= self.llm.temperature <= 2.0):
            errors.append("LLM_TEMPERATURE must be between 0.0 and 2.0")

        if self.logging.max_bytes < 1024:
            errors.append("LOG_MAX_BYTES must be at least 1024 bytes")

        return errors


# Global configuration instance
config = AppConfig.from_env()
