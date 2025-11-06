"""
Configuration module for Vanna AI application.
Manages environment variables and application settings.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
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
        return cls(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS"))
            if os.getenv("LLM_MAX_TOKENS")
            else None,
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
            max_tool_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "50")),
            stream_responses=os.getenv("AGENT_STREAM_RESPONSES", "true").lower()
            == "true",
            auto_save_conversations=os.getenv(
                "AGENT_AUTO_SAVE_CONVERSATIONS", "true"
            ).lower()
            == "true",
            include_thinking_indicators=os.getenv(
                "AGENT_THINKING_INDICATORS", "true"
            ).lower()
            == "true",
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
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            file=os.getenv("LOG_FILE", "logs/vanna_app.log"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),  # 10MB default
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        )


@dataclass
class AppConfig:
    """Main application configuration."""

    database: DatabaseConfig
    llm: LLMConfig
    agent: AgentConfig
    logging: LoggingConfig
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
            logging=LoggingConfig.from_env(),
            schema_file=os.getenv("SCHEMA_FILE", "structure.txt"),
            chroma_db_path=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
            app_port=int(os.getenv("APP_PORT", "8000")),
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
