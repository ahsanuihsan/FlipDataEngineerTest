# Pokemon Ability Data Engineering Test - Flip

## 📋 Overview

This project is a FastAPI-based microservice that fetches Pokemon ability data from PokeAPI, normalizes the data, stores it in a SQLite database, and returns structured JSON responses.

## 🏗️ Architecture

### System Components
- **FastAPI**: Modern web framework for building APIs
- **SQLite**: Lightweight relational database for data storage
- **PokeAPI**: External API for Pokemon data
- **Docker**: Containerization for easy deployment

### Data Flow
1. Client sends JSON input with `raw_id`, `user_id`, and `pokemon_ability_id`
2. FastAPI receives and validates the input
3. Application fetches ability data from PokeAPI
4. Effect entries are normalized and stored in SQLite database
5. Response is formatted and returned to client

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ (for local development)
- Git

### Running with Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd flip-data-engineer-test

# Build and run with Docker Compose
docker-compose up --build

# The API will be available at http://localhost:8000
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### 1. Process Pokemon Ability
**Endpoint:** `POST /process-ability`

**Request Body:**
```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "pokemon_ability_id": "150"
}
```

**Response:**
```json
{
  "raw_id": "7dsa8d7sa9dsa",
  "user_id": "5199434",
  "returned_entries": [
    {
      "effect": "Pokémon mit dieser Fähigkeit kopieren einen zufälligen Gegner...",
      "language": {
        "name": "de",
        "url": "https://pokeapi.co/api/v2/language/6/"
      },
      "short_effect": "Verwandelt sich beim Betreten des Kampfes in den Gegner."
    },
    {
      "effect": "This Pokémon transforms into a random opponent upon entering battle...",
      "language": {
        "name": "en",
        "url": "https://pokeapi.co/api/v2/language/9/"
      },
      "short_effect": "Transforms upon entering battle."
    }
  ],
  "pokemon_list": ["ditto"]
}
```

### 2. Retrieve Stored Abilities
**Endpoint:** `GET /abilities/{raw_id}/{user_id}`

Returns all stored abilities for a specific raw_id and user_id combination.

### 3. Health Check
**Endpoint:** `GET /health`

Returns API health status.

## 🗄️ Database Schema

```sql
CREATE TABLE pokemon_abilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_id VARCHAR(13) NOT NULL,
    user_id VARCHAR(7) NOT NULL,
    pokemon_ability_id INTEGER NOT NULL,
    effect TEXT NOT NULL,
    language TEXT NOT NULL,
    short_effect TEXT NOT NULL
);
```

## 🧪 Testing the API

### Using cURL

```bash
# Test the API
curl -X POST "http://localhost:8000/process-ability" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_id": "7dsa8d7sa9dsa",
    "user_id": "5199434",
    "pokemon_ability_id": "150"
  }'

# Retrieve stored data
curl "http://localhost:8000/abilities/7dsa8d7sa9dsa/5199434"
```

### Using Python

```python
import requests

url = "http://localhost:8000/process-ability"
data = {
    "raw_id": "7dsa8d7sa9dsa",
    "user_id": "5199434",
    "pokemon_ability_id": "150"
}

response = requests.post(url, json=data)
print(response.json())
```

## 🎯 Technical Decisions & Rationale

### 1. Why FastAPI?
- **Performance**: Built on Starlette and Pydantic, offering high performance
- **Async Support**: Native async/await support for concurrent API calls
- **Automatic Documentation**: Built-in Swagger UI and ReDoc
- **Type Safety**: Pydantic models provide data validation
- **Modern**: Python 3.9+ with type hints

### 2. Why SQLite?
- **Simplicity**: No separate database server needed
- **Portability**: Single file database, easy to backup and move
- **Zero Configuration**: Works out of the box
- **Sufficient for Test**: Perfect for development and testing scenarios
- **Easy to Containerize**: No additional containers needed

**Production Alternative**: For production, I would recommend PostgreSQL for:
- Better concurrency handling
- ACID compliance at higher scale
- More advanced features (JSON types, full-text search)
- Better horizontal scaling options

### 3. Why SQLAlchemy ORM?
- **Database Abstraction**: Easy to switch databases if needed
- **Type Safety**: Python models map to database tables
- **Query Builder**: Pythonic way to build queries
- **Migration Support**: Works with Alembic for schema migrations

### 4. Data Storage Approach
- **Normalization**: Each effect entry is stored as a separate row
- **JSON Serialization**: Language dict stored as JSON text for flexibility
- **Indexing**: raw_id and user_id can be indexed for faster queries

### 5. Error Handling
- **HTTP Status Codes**: Proper use of 404, 500, etc.
- **Detailed Error Messages**: Help debug issues
- **Timeout Configuration**: 30s timeout for PokeAPI calls

### 6. Docker Benefits
- **Consistency**: Same environment in dev and prod
- **Isolation**: No dependency conflicts
- **Easy Deployment**: Single command to run everything
- **Scalability**: Easy to scale horizontally with orchestration tools

## 📊 Data Architecture (Question 2)

### Staging → ODS → Data Warehouse Flow

```
┌─────────────────┐
│  Source: API    │
│   (PokeAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│        STAGING LAYER                │
│  - Raw JSON from PokeAPI            │
│  - Minimal transformation           │
│  - Append-only storage              │
│  - Keep original payload            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  OPERATIONAL DATA STORE (ODS)       │
│  - Normalized tables                │
│  - Current state of data            │
│  - pokemon_abilities table          │
│  - Real-time access                 │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     DATA WAREHOUSE                  │
│  - Dimensional model                │
│  - Fact: ability_usage              │
│  - Dim: pokemon, abilities, users   │
│  - Aggregated metrics               │
│  - Historical tracking              │
└─────────────────────────────────────┘
```

### Layer Details:

**1. STAGING LAYER**
- Purpose: Land raw data from source
- Schema: Flexible/schema-on-read
- Retention: 30-90 days
- Format: JSON/Parquet
- Example table: `stg_pokemon_abilities_raw`

**2. ODS LAYER**
- Purpose: Current operational data
- Schema: Normalized (3NF)
- Retention: Based on business needs
- Tables:
  - `pokemon_abilities` (current implementation)
  - `pokemon_master`
  - `language_master`
  - `ability_master`

**3. DATA WAREHOUSE LAYER**
- Purpose: Analytics and reporting
- Schema: Star/Snowflake schema
- Retention: Historical data (years)
- Tables:
  - `fact_ability_requests`
  - `dim_pokemon`
  - `dim_abilities`
  - `dim_users`
  - `dim_date`

### ETL Pipeline:
1. **Extract**: Pull from PokeAPI → Staging
2. **Transform**: Normalize → ODS
3. **Load**: Aggregate → DWH

## 🔧 Future Enhancements

1. **PostgreSQL Support**: Add environment variable to switch databases
2. **Caching**: Implement Redis for frequently accessed data
3. **Authentication**: Add API key or JWT authentication
4. **Rate Limiting**: Prevent API abuse
5. **Logging**: Structured logging with ELK stack
6. **Monitoring**: Prometheus metrics and Grafana dashboards
7. **CI/CD**: GitHub Actions for automated testing and deployment
8. **Data Validation**: More comprehensive input validation
9. **Batch Processing**: Support bulk ability processing
10. **API Versioning**: Support multiple API versions

## 📝 Project Structure

```
flip-data-engineer-test/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── README.md              # This file
├── data/                  # SQLite database directory (created at runtime)
└── tests/                 # Unit tests (to be added)
```

## 👨‍💻 Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions with docstrings

### Adding New Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## 📞 Support

For questions or issues, please open an issue in the repository.

## 📄 License

This project is created for Flip Data Engineer technical test.

---

**Author**: Ihsan Ahsanu Amala
**Date**: February 2026
**Version**: 1.0.0
