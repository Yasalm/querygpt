# QueryGPT

An AI agent in your terminal that can connect to databases and generate insights using natural language queries. 
- It leverage LLM to generate documentation for each table and column and also any foreign relationship, and roleplay as data documenation expert to generate possible bussiness usage of them.

Check out this [article](https://yasalm.github.io/yasir-s/an-ai-agent-to-interact-with-databases) for techincal deep dive 


## Getting Started

### Requirements
- Python 3.7 or higher
- API key for Google Gemini (currently the only supported LLM)

### Installation

   Clone the repository:
   ```bash
   git clone git@github.com:Yasalm/querygpt.git
   cd querygpt
   ```

   ```bash
   # Install Poetry if you don't have it already
   # On macOS/Linux/WSL:
   brew install poetry
   
   # Install dependencies using Poetry
   poetry install
   ```

   Optional dependency groups can be installed as needed:
   
   | Database Support | Installation Command |
   |------------------|----------------------|
   | PostgreSQL       | `poetry install --with postgres` |
   | ClickHouse       | `poetry install --with clickhouse` |
   | All Databases    | `poetry install --with all` |

### Running QueryGPT

QueryGPT is an agentic system that uses a collection of tools to automatically analyze your database and answer complex questions without requiring SQL knowledge.

1. Use the CLI commands:
   ```bash
   # First, generate documentation from your database sources
   poetry run querygpt generate
      -> Generation complete. You can now use `querygpt query` to interact with the agent.
   
   # Then run queries in natural language
   poetry run querygpt query "Analyze the rental patterns across different film categories and identify which categories show seasonal trends, comparing summer vs winter rentals for the past two years"
      -> {
         "agent_answer": "...",
         "sql_result": [
            {
               ...
            }
         ],
         ...
      }
   ```

2. Start the API server and use it:
   ```bash
   # Start the API server
   python -m serving.serving
   
   # Then query the API
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Find customers who spent more than the average in 2022, break down their spending by film category, and recommend three films they haven't watched based on their preferences"}'
   ```

### Database Configuration setups:

1. Create a `.env` file in the project root with your database credentials and API keys:
   ```
   # Create a .env file with the appropriate variables for your database type
   # PostgreSQL connection variables
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database
   
   # LLM API keys
   GEMINI_API_KEY=your_gemini_key
   ```

   Note: See the configuration examples below for the specific environment variables needed for each database type.

2. Configure your database connections in `config/config.yaml`:

   **PostgreSQL/ClickHouse Configuration:**
   ```yaml
   sources:
     default_source:
       engine: postgres  # Use 'postgres' or 'clickhouse'
       user: ${env:DB_USER}
       password: ${env:DB_PASSWORD}
       host: ${env:DB_HOST}
       port: ${env:DB_PORT}
       dbname: ${env:DB_NAME}
       schema_query_path: core/sql/postgres.sql  # Use appropriate SQL path
   ```

   **Oracle Configuration:**
   ```yaml
   sources:
     oracle_source:
       engine: oracle
       user: ${env:ORACLE_USER}
       password: ${env:ORACLE_PASSWORD}
       dsn: ${env:ORACLE_HOST}:${env:ORACLE_PORT}/${env:ORACLE_SERVICE}
       schema_query_path: /core/sql/postgres.sql
   ```

   You can configure multiple database sources in the same config file.

### Example Database Setup

You can use the Pagila example database (a sample movie rental database) to experiment with QueryGPT:

1. Use the provided Makefile commands to set up the example database:
   ```bash
   # Build and run the Pagila database
   make generate-pagila-db
   
   # To stop and remove the database container when done
   make cleanup-pagila-db
   
   # For help with available commands
   make help
   ```

2. Add the Pagila configuration to your config file:

   After setting up the Pagila database, add its configuration located at `example_databases/pagila/config.yaml` to the `sources` section 
   in your `config/config.yaml` file:

   ```yaml
   # Add this to the sources section in your config/config.yaml
   pagila:
     engine: postgres
     user: postgres
     password: password
     host: localhost
     port: 5432
     dbname: pagila
     schema_query_path: /core/sql/postgres.sql
   ```

## Configuration

The default configuration includes:
- **Index settings**: Vector search settings for documentation, including embedding dimensions and similarity metrics
- **Source database connections**: Connect to multiple databases with different credentials and schemas
- **Internal database**: Storage for metadata, documentation, query history, and access policies
- **LLM settings**: Configure your preferred AI model provider (OpenAI, Anthropic, etc.), model parameters, and API credentials

All configuration options are documented with examples in the `config/config.yaml` file. You can customize these settings to match your specific requirements.
## Supported databases

QueryGPT currently suppoert the followingå:

| Database | Status | Configuration |
|----------|--------|--------------|
| Postgres | ✅ Fully supported | - |
| Clickhouse | ✅ Fully supported | - |
| Oracle | ✅ Fully supported | - |
| MySQL | 🔄 In development | - |

## Supported LLM Models

QueryGPT currently supports Google Gemini with ongoing development to add more providers. Below is the current support status:

| Provider | Status | Configuration |
|----------|--------|--------------|
| Google | ✅ Fully supported | `GEMINI_API_KEY` |
| OpenAI | 🔄 In development | Coming soon |
| Anthropic | 🔄 In development | Coming soon |
| Local | 🔄 In development | Coming soon |
