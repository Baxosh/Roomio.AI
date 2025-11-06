import sys

from vanna import Agent
from vanna.core.agent import AgentConfig as VannaAgentConfig
from vanna.core.agent.config import UiFeatures
from vanna.core.registry import ToolRegistry
from vanna.integrations.chromadb import ChromaAgentMemory
from vanna.integrations.openai import OpenAILlmService
from vanna.integrations.postgres import PostgresRunner
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
)

from config import config
from custom_prompt import SchemaAwarePromptBuilder
from logging_config import setup_logging
from user_resolver import SimpleUserResolver

# Setup logging with configuration
logger = setup_logging(
    log_level=config.logging.level,
    log_file=config.logging.file,
    max_bytes=config.logging.max_bytes,
    backup_count=config.logging.backup_count,
)

logger.info("=" * 80)
logger.info("Starting Vanna AI Application")
logger.info("=" * 80)

# Validate configuration
logger.info("Validating configuration...")
validation_errors = config.validate()
if validation_errors:
    logger.error("Configuration validation failed:")
    for error in validation_errors:
        logger.error(f"  - {error}")
    logger.error("Exiting due to configuration errors")
    sys.exit(1)
logger.info("Configuration validated successfully")

logger.info("Initializing OpenAI LLM Service with DeepSeek")
logger.info(f"LLM Config: {config.llm}")
llm = OpenAILlmService(
    model=config.llm.model,
    api_key=config.llm.api_key,
    base_url=config.llm.base_url,
)
logger.info("LLM Service initialized successfully")

logger.info("Initializing database connection")
logger.info(f"Database Config: {config.database}")

db_tool = RunSqlTool(
    sql_runner=PostgresRunner(
        host=config.database.host,
        port=config.database.port,
        database=config.database.database,
        user=config.database.user,
        password=config.database.password,
    )
)
logger.info("Database tool initialized successfully")


logger.info("Initializing ChromaDB agent memory")
logger.info(f"ChromaDB path: {config.chroma_db_path}")
agent_memory = ChromaAgentMemory(
    collection_name="vanna_memory", persist_directory=config.chroma_db_path
)
save_memory_tool = SaveQuestionToolArgsTool(agent_memory)
search_memory_tool = SearchSavedCorrectToolUsesTool(agent_memory)
logger.info("Agent memory initialized successfully")

logger.info("Initializing user resolver")
user_resolver = SimpleUserResolver(sql_runner=db_tool.sql_runner)

# Register tools
logger.info("Registering tools")
tools = ToolRegistry()
tools.register_local_tool(db_tool, access_groups=["admin", "user"])
tools.register_local_tool(save_memory_tool, access_groups=["admin"])
tools.register_local_tool(search_memory_tool, access_groups=["admin", "user"])
tools.register_local_tool(VisualizeDataTool(), access_groups=["admin", "user"])
logger.info("Tools registered successfully")

logger.info("Creating agent configuration")
logger.info(
    f"Agent Config: max_iterations={config.agent.max_tool_iterations}, stream={config.agent.stream_responses}"
)
agent_config = VannaAgentConfig(
    max_tool_iterations=config.agent.max_tool_iterations,
    stream_responses=config.agent.stream_responses,
    auto_save_conversations=config.agent.auto_save_conversations,
    include_thinking_indicators=config.agent.include_thinking_indicators,
    temperature=config.llm.temperature,
    max_tokens=config.llm.max_tokens,
    ui_features=UiFeatures(
        feature_group_access={
            "tool_names": ["admin", "developer"],
            "tool_arguments": ["admin"],
            "tool_error": ["admin", "support"],
            "tool_invocation_message_in_chat": [],  # All users
        }
    ),
)
logger.info("Agent configuration created")

# Create your agent
logger.info("Creating Vanna agent")
logger.info(f"Schema file: {config.schema_file}")
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    config=agent_config,
    system_prompt_builder=SchemaAwarePromptBuilder(
        sql_runner=db_tool.sql_runner, schema_file=config.schema_file
    ),
)
logger.info("Vanna agent created successfully")

logger.info("Starting FastAPI server")
server = VannaFastAPIServer(agent)
logger.info("=" * 80)
logger.info("Vanna AI Application is ready to serve requests")
logger.info("=" * 80)
server.run()
