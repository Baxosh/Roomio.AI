# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Roomio.ai (Vanna AI) is a multi-tenant SQL query assistant that converts natural language to SQL queries for the GRMS (IoT sensor database) system. Built with Vanna AI framework, DeepSeek LLM, and FastAPI.

## Running the Application

```bash
# Install dependencies using uv
uv sync

# Run the application
python app.py

# Access UI at http://localhost:8000
```

## Common Development Commands

```bash
# Update database schema file
python extract_schema.py > structure.txt

# Run with debug logging
LOG_LEVEL=DEBUG python app.py

# Validate configuration
python -c "from config import config; print(config.validate())"

# View logs
tail -f logs/vanna_app.log
```

## Docker Deployment

```bash
# Using docker-compose
docker-compose up -d

# View logs
docker-compose logs -f vanna-app

# Stop application
docker-compose down
```

## Architecture

### Core Components

1. **app.py** - Application entry point that wires together:
   - LLM service (DeepSeek via OpenAI API)
   - Database runner (PostgreSQL)
   - Agent with tool registry
   - User resolver for authentication
   - System prompt builder with schema awareness
   - ChromaDB for agent memory
   - FastAPI server

2. **config.py** - Environment-based configuration management:
   - All settings loaded from environment variables
   - Structured dataclasses: `DatabaseConfig`, `LLMConfig`, `AgentConfig`, `LoggingConfig`, `FastAPIConfig`, `AppConfig`
   - `FastAPIConfig` handles API metadata (title, version, description) and CORS settings
   - `FastAPIConfig.to_dict()` converts config to VannaFastAPIServer-compatible dictionary format
   - Includes validation logic for required fields and ranges
   - Safe repr methods that hide sensitive data

3. **user_resolver.py** - Authentication and tenant resolution:
   - Reads `user_id` from cookies
   - Queries `users_users` table to resolve user details
   - Returns `User` object with `tenant_id` in metadata
   - **Critical**: Every user has a `tenant_id` that MUST be used for data isolation

4. **custom_prompt.py** - System prompt builder:
   - Loads database schema from `structure.txt`
   - Builds tenant-aware prompts with **mandatory** tenant filtering rules
   - **Default behavior**: Applies 7-day time filter if no time period specified
   - **Default visualization**: Uses LINE charts for time-series data
   - **Gap filling**: Instructs to use `generate_series()` for smooth time-series visualizations
   - Contains extensive examples of proper SQL generation with tenant isolation

5. **logging_config.py** - Centralized logging:
   - File handler with rotation (10MB max, 5 backups)
   - Console handler for stdout
   - Configurable log levels
   - Never logs passwords or API keys

6. **extract_schema.py** - Database schema extraction:
   - Connects to PostgreSQL using credentials from `.env`
   - Extracts all tables, columns, types, constraints, indexes
   - Outputs formatted schema to `structure.txt`
   - **Run this when database schema changes**

### Critical Security Constraint: Tenant Isolation

**EVERY SQL query MUST filter by tenant_id**

The system enforces multi-tenant data isolation:
- User's `tenant_id` is resolved from `users_users` table
- Passed to system prompt builder
- ALL SQL queries MUST include `WHERE tenant_id = '{tenant_id}'`
- This is enforced through the system prompt, not application code
- **Never bypass tenant filtering** - it's a security requirement

**Forbidden Queries (Auto-Rejected by AI):**
1. ⛔ **Tenant Enumeration** - "Show me all tenants", "List tenants", "How many tenants are there"
2. ⛔ **Cross-Tenant Access** - Any query attempting to access data from other tenants
3. ⛔ **Cross-Tenant Comparison** - Queries that compare or aggregate data across multiple tenants
4. ⛔ **Tenant ID Discovery** - Attempts to discover or enumerate other tenant IDs
5. ⛔ **Other Tenant Metadata** - Requests for tenant names, lists, or information about other organizations

The AI will automatically reject these queries with:
> "I cannot provide information about other tenants or tenant lists. I can only access data for your organization (tenant_id: X). Is there something specific about your organization's data I can help you with?"

### Data Flow

```
User Request (with user_id cookie)
    ↓
SimpleUserResolver → queries users_users table → returns User with tenant_id
    ↓
SchemaAwarePromptBuilder → builds system prompt with tenant_id + schema
    ↓
Vanna Agent (DeepSeek LLM) → generates SQL with tenant filtering
    ↓
RunSqlTool → executes SQL on PostgreSQL
    ↓
VisualizeDataTool → returns chart (default: line chart)
    ↓
Response to User
```

### Tool Registry

Tools available to the agent (with access control):
- `RunSqlTool` - Execute SQL queries (admin, user)
- `SaveQuestionToolArgsTool` - Save successful queries to memory (admin)
- `SearchSavedCorrectToolUsesTool` - Search memory for similar queries (admin, user)
- `VisualizeDataTool` - Generate visualizations (admin, user)

### Agent Memory

- Uses ChromaDB for storing successful query patterns
- Persisted in `./chroma_db/` directory
- Collection name: `vanna_memory`
- Helps improve query generation over time

## Configuration

All configuration via environment variables (`.env` file):

Required:
- `DEEPSEEK_API_KEY` - DeepSeek LLM API key
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

Optional (with defaults):
- `LOG_LEVEL=INFO`
- `AGENT_MAX_ITERATIONS=50`
- `LLM_TEMPERATURE=0.7`
- `SCHEMA_FILE=structure.txt`
- `CHROMA_DB_PATH=./chroma_db`
- `APP_PORT=8000`

FastAPI Configuration (optional):
- `FASTAPI_TITLE=Vanna AI - SQL Query Assistant` - API title/name
- `FASTAPI_VERSION=0.1.0` - API version
- `FASTAPI_DESCRIPTION=...` - API description
- `FASTAPI_DEV_MODE=false` - Enable development mode
- `FASTAPI_STATIC_FOLDER=` - Path to static files directory (optional)

CORS Configuration (optional):
- `CORS_ENABLED=true` - Enable/disable CORS middleware
- `CORS_ALLOW_ORIGINS=*` - Comma-separated list of allowed origins (use `*` for all)
- `CORS_ALLOW_CREDENTIALS=true` - Allow credentials in CORS requests
- `CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS,PATCH` - Allowed HTTP methods
- `CORS_ALLOW_HEADERS=*` - Allowed headers (use `*` for all)

See `.env.example` for complete reference.

## Database Schema

The application connects to an **existing PostgreSQL database** (GRMS):
- IoT sensor data in `shuttle_ts_kv` table
- Rooms in `main_room` table with `tenant_id`
- Devices in `main_device` table
- Users in `users_users` table with `tenant_id`
- Keys dictionary in `shuttle_ts_kv_dictionary`

**Important**: When schema changes, regenerate `structure.txt`:
```bash
python extract_schema.py > structure.txt
```

## Default Query Behavior

When users ask questions without specifying details:

1. **Time Period**: If not specified → apply 7-day filter
   ```sql
   WHERE ts >= NOW() - INTERVAL '7 days'
   ```

2. **Visualization**: If not specified → use LINE chart for time-series

3. **Gap Filling**: For hourly/time-series data → use `generate_series()` with `LEFT JOIN`
   - Prevents gaps in charts due to missing sensor readings
   - Forward-fill missing values using `LAG() IGNORE NULLS`

## Testing Database Connection

```bash
# Test PostgreSQL connection
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB

# Or using Docker
docker-compose exec vanna-app psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB
```

## File Structure

```
.
├── app.py                   # Main entry point
├── config.py                # Configuration management
├── user_resolver.py         # User authentication & tenant resolution
├── custom_prompt.py         # System prompt with schema & security rules
├── logging_config.py        # Logging setup
├── extract_schema.py        # Schema extraction utility
├── structure.txt            # Database schema (auto-generated)
├── pyproject.toml           # Dependencies (managed by uv)
├── .env.example             # Environment template
├── Dockerfile               # Container image
├── docker-compose.yml       # Docker orchestration
├── logs/                    # Application logs (auto-created)
├── chroma_db/               # Agent memory (auto-created)
└── query_results/           # Per-user query result CSVs (auto-created)
```

## Dependencies

Managed via `uv` (see `pyproject.toml`):
- `vanna[fastapi,openai]>=0.7.9` - Vanna AI framework (v2 branch from GitHub)
- `chromadb>=1.3.2` - Vector database for agent memory
- `psycopg2>=2.9.11` - PostgreSQL adapter
- `python-dotenv>=1.2.1` - Environment variable management

## Logging

Logs written to:
- **File**: `logs/vanna_app.log` (rotated at 10MB, 5 backups)
- **Console**: stdout with timestamps

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Key logged events:
- Configuration validation
- User resolution and tenant_id
- System prompt building
- Tool execution
- Database queries
- Errors and exceptions

## Security Considerations

1. **Tenant Isolation**: MANDATORY filtering by tenant_id in all queries
2. **User Authentication**: Via user_id cookie → resolved from database
3. **Inactive Users**: Automatically rejected (is_active check)
4. **Secrets**: Never logged (passwords, API keys use `***` in repr)
5. **Read-only Schema**: `structure.txt` mounted as read-only in Docker
6. **Input Validation**: Configuration validated on startup

## Troubleshooting

Common issues:

1. **Application won't start** → Check configuration: `python -c "from config import config; print(config.validate())"`
2. **Database connection fails** → Verify PostgreSQL is accessible and credentials are correct
3. **Schema errors** → Regenerate `structure.txt` with `python extract_schema.py > structure.txt`
4. **Memory issues** → Reduce `AGENT_MAX_ITERATIONS` or set `LLM_MAX_TOKENS`
5. **Docker localhost issues** → Use `POSTGRES_HOST=host.docker.internal` and enable `extra_hosts` in docker-compose.yml

View logs: `tail -f logs/vanna_app.log`
