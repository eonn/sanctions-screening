# Sanctions Screening Platform

A production-quality sanctions screening platform using state-of-the-art natural language processing (BERT), Fuzzy Logic for name similarity, and industry best practices. The platform ingests names/entities, screens against dynamic sanctions lists, and outputs robust match decisions with clear audit trails.

**Author:** Eon (Himanshu Shekhar)  
**Email:** eonhimanshu@gmail.com  
**GitHub:** https://github.com/eonn/sanctions-screening  
**Created:** 2024

## Features

- **BERT-based NLP**: Semantic similarity matching using state-of-the-art transformer models
- **Fuzzy Logic Matching**: Multiple algorithms for name similarity (Levenshtein, token-based, etc.)
- **Comprehensive Screening**: Exact, fuzzy, and semantic matching with configurable thresholds
- **Audit Trail**: Complete logging of all screening activities and decisions
- **RESTful API**: Full-featured API with OpenAPI documentation
- **Web UI**: Modern, responsive web interface for easy interaction
- **Real-time Analytics**: Screening statistics and performance metrics
- **Production Ready**: Health checks, monitoring, error handling, and security features

## Architecture

### Core Components

1. **NLP Service** (`app/services/nlp_service.py`)
   - BERT-based semantic similarity using sentence-transformers
   - Name preprocessing and normalization
   - Embedding generation and similarity calculation

2. **Fuzzy Service** (`app/services/fuzzy_service.py`)
   - Multiple fuzzy matching algorithms
   - Weighted scoring system
   - Token-based and character-based matching

3. **Screening Service** (`app/services/screening_service.py`)
   - Orchestrates matching algorithms
   - Risk scoring and decision logic
   - Comprehensive match analysis

4. **Database Models** (`app/models/database.py`)
   - Entity management
   - Sanctions list storage
   - Screening results and audit logs

### Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: SQLAlchemy with SQLite/PostgreSQL support
- **NLP**: Transformers, sentence-transformers, scikit-learn
- **Fuzzy Matching**: fuzzywuzzy, rapidfuzz
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Testing**: pytest with coverage reporting
- **Monitoring**: Prometheus metrics

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sanctions-screening-platform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -c "from app.core.database import init_db; init_db()"
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The application will be available at:
- Web UI: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Usage

### Web Interface

1. Open http://localhost:8000 in your browser
2. Fill in the entity information (name, type, aliases, etc.)
3. Click "Screen Entity" to perform screening
4. View results with detailed match information

### API Usage

#### Single Entity Screening

```bash
curl -X POST "http://localhost:8000/api/v1/screen" \
     -H "Content-Type: application/json" \
     -d '{
       "entity": {
         "name": "John Smith",
         "aliases": ["Johnny Smith", "J. Smith"],
         "date_of_birth": "1980-05-15",
         "nationality": "American",
         "passport_number": "A12345678",
         "entity_type": "individual"
       },
       "include_metadata": true
     }'
```

#### Batch Screening

```bash
curl -X POST "http://localhost:8000/api/v1/screen/batch" \
     -H "Content-Type: application/json" \
     -d '[
       {
         "entity": {
           "name": "Alice Johnson",
           "entity_type": "individual"
         }
       },
       {
         "entity": {
           "name": "John Smith",
           "entity_type": "individual"
         }
       }
     ]'
```

#### Get Analytics

```bash
curl "http://localhost:8000/analytics/screenings?start_date=2023-01-01&end_date=2023-12-31"
```

### Configuration

The platform can be configured using environment variables or a `.env` file:

```bash
# Application settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./sanctions_screening.db

# BERT Model
BERT_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Matching thresholds
SIMILARITY_THRESHOLD=0.85
FUZZY_THRESHOLD=0.8

# Logging
LOG_LEVEL=INFO
```

## API Reference

### Endpoints

#### Screening
- `POST /api/v1/screen` - Screen a single entity
- `POST /api/v1/screen/batch` - Screen multiple entities

#### Entities
- `GET /api/v1/entities` - List entities
- `GET /api/v1/entities/{id}` - Get entity by ID

#### Sanctions Lists
- `GET /api/v1/sanctions` - List sanctions entries
- `GET /api/v1/sanctions/{id}` - Get sanctions entry by ID

#### Analytics
- `GET /analytics/screenings` - Get screening statistics

#### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - API documentation

### Request/Response Schemas

#### Screening Request
```json
{
  "entity": {
    "name": "string",
    "aliases": ["string"],
    "date_of_birth": "YYYY-MM-DD",
    "nationality": "string",
    "passport_number": "string",
    "entity_type": "individual|organization"
  },
  "include_metadata": true,
  "threshold_override": 0.85
}
```

#### Screening Response
```json
{
  "screening_id": 1,
  "entity_id": 1,
  "entity_name": "string",
  "screening_date": "2023-01-01T00:00:00Z",
  "overall_risk_score": 0.95,
  "decision": "block|review|clear",
  "confidence_score": 0.95,
  "processing_time_ms": 150,
  "matches": [
    {
      "sanctions_entry_id": 1,
      "entity_name": "string",
      "source": "OFAC",
      "list_name": "SDN List",
      "match_score": 0.95,
      "match_type": "exact|fuzzy|bert",
      "matched_fields": ["name", "date_of_birth"],
      "risk_score": 0.95,
      "match_details": {}
    }
  ],
  "metadata": {}
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Test Structure

- `tests/test_screening.py` - Unit tests for screening logic
- `tests/test_integration.py` - Integration tests for API endpoints

## Deployment

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t sanctions-screening .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 sanctions-screening
   ```

### Production Considerations

1. **Database**: Use PostgreSQL for production
2. **Security**: Configure proper authentication and authorization
3. **Monitoring**: Set up Prometheus and Grafana for metrics
4. **Logging**: Configure structured logging with ELK stack
5. **Caching**: Implement Redis for performance optimization
6. **Load Balancing**: Use nginx or similar for high availability

## Performance

### Benchmarks

- **Single Screening**: ~100-500ms (depending on sanctions list size)
- **Batch Screening**: ~50-200ms per entity
- **BERT Model Loading**: ~2-5 seconds (first time)
- **Database Queries**: <10ms for indexed lookups

### Optimization Tips

1. **Database Indexing**: Ensure proper indexes on name fields
2. **Caching**: Cache BERT embeddings for frequently screened names
3. **Batch Processing**: Use batch endpoints for multiple entities
4. **Model Optimization**: Use quantized models for faster inference

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the test examples for usage patterns

## Roadmap

- [ ] Real-time sanctions list updates
- [ ] Advanced machine learning models
- [ ] Multi-language support
- [ ] Graph-based relationship analysis
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Integration with external data sources 
