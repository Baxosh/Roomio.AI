"""
Roomio.ai - Multi-tenant SQL Query Assistant

Main application entry point that configures and runs the Vanna AI system.
"""

import sys
from typing import Final

from vanna import Agent
from vanna.core.agent import AgentConfig as VannaAgentConfig
from vanna.core.agent.config import UiFeatures
from vanna.core.registry import ToolRegistry
from vanna.integrations.chromadb import ChromaAgentMemory
from vanna.integrations.local import LocalFileSystem
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
from custom_workflow import RoomioWorkflowHandler
from logging_config import setup_logging
from user_resolver import SimpleUserResolver

# Constants for access control groups
ACCESS_GROUP_ADMIN: Final[str] = "admin"
ACCESS_GROUP_USER: Final[str] = "user"
ACCESS_GROUP_DEVELOPER: Final[str] = "developer"
ACCESS_GROUP_SUPPORT: Final[str] = "support"

# Constants for agent memory
MEMORY_COLLECTION_NAME: Final[str] = "vanna_memory"

# Constants for query results storage
QUERY_RESULTS_DIR: Final[str] = "./query_results"

# Setup logging with configuration
logger = setup_logging(
    log_level=config.logging.level,
    log_file=config.logging.file,
    max_bytes=config.logging.max_bytes,
    backup_count=config.logging.backup_count,
)

# Validate configuration
validation_errors = config.validate()
if validation_errors:
    logger.error("Configuration validation failed:")
    for error in validation_errors:
        logger.error(f"  - {error}")
    logger.error("Exiting due to configuration errors")
    sys.exit(1)

llm = OpenAILlmService(
    model=config.llm.model,
    api_key=config.llm.api_key,
    base_url=config.llm.base_url,
)

file_system = LocalFileSystem(working_directory=QUERY_RESULTS_DIR)

db_tool = RunSqlTool(
    sql_runner=PostgresRunner(
        host=config.database.host,
        port=config.database.port,
        database=config.database.database,
        user=config.database.user,
        password=config.database.password,
    ),
    file_system=file_system,
)
agent_memory = ChromaAgentMemory(
    collection_name=MEMORY_COLLECTION_NAME, persist_directory=config.chroma_db_path
)
save_memory_tool = SaveQuestionToolArgsTool()
search_memory_tool = SearchSavedCorrectToolUsesTool()

user_resolver = SimpleUserResolver(sql_runner=db_tool.sql_runner)

# Register tools
tools = ToolRegistry()
tools.register_local_tool(
    db_tool, access_groups=[ACCESS_GROUP_ADMIN, ACCESS_GROUP_USER]
)
tools.register_local_tool(save_memory_tool, access_groups=[ACCESS_GROUP_ADMIN])
tools.register_local_tool(
    search_memory_tool, access_groups=[ACCESS_GROUP_ADMIN, ACCESS_GROUP_USER]
)
tools.register_local_tool(
    VisualizeDataTool(), access_groups=[ACCESS_GROUP_ADMIN, ACCESS_GROUP_USER]
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
            "tool_names": [ACCESS_GROUP_ADMIN, ACCESS_GROUP_DEVELOPER],
            "tool_arguments": [ACCESS_GROUP_ADMIN],
            "tool_error": [ACCESS_GROUP_ADMIN, ACCESS_GROUP_SUPPORT],
            "tool_invocation_message_in_chat": [],  # All users
        }
    ),
)

agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory,
    config=agent_config,
    system_prompt_builder=SchemaAwarePromptBuilder(
        sql_runner=db_tool.sql_runner, schema_file=config.schema_file
    ),
    workflow_handler=RoomioWorkflowHandler(),  # Custom Roomio-branded workflow handler
)

# Create server with configuration dictionary
server = VannaFastAPIServer(agent, config=config.fastapi.to_dict())  # pyright: ignore

server.run(port=config.app_port)
