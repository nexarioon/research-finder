# Research Prospect Finder - Architecture Report

## Current Architecture

The application follows a clean layered architecture:

```
CLI Layer (cli/)
    ├── screens/          # UI presentation
    └── main.py           # Entry point

Application Layer (application/)
    ├── discovery_service.py   # Business discovery orchestration
    ├── ranking_service.py     # Candidate scoring orchestration
    └── ai_service.py          # AI analysis orchestration

Domain Layer (domain/)
    └── models.py              # Business logic models

Providers (providers/)
    ├── base.py                # Abstract interfaces
    ├── nominatim.py           # OpenStreetMap business search
    ├── location.py            # Geocoding services
    ├── website.py             # Website analysis
    ├── openai_provider.py     # AI provider (OpenAI-compatible)
    └── email.py               # Email sending

Database (database/)
    ├── connection.py          # SQLAlchemy setup
    ├── models.py              # ORM models
    ├── repositories.py        # Business CRUD
    ├── scoring_repository.py  # Score management
    ├── website_repository.py  # Website analysis CRUD
    ├── ai_repository.py       # AI analysis CRUD
    ├── opportunity_repository.py  # Opportunities & topics CRUD
    └── outreach_repository.py     # Outreach CRUD

Services (services/)
    ├── scoring.py             # Deterministic scoring logic
    └── email_templates.py     # Email templates

Config (config/)
    ├── settings.py            # Pydantic settings
    └── logging.py             # Structured logging
```

## Separation of Concerns

### Well-Separated Components
- **Scoring logic** (`services/scoring.py`): Pure business logic, no CLI dependency
- **Email templates** (`services/email_templates.py`): Pure template generation
- **Database repositories**: All CRUD operations are independent of CLI
- **Providers**: All external service integrations are behind abstractions
- **Domain models**: Pure dataclasses with no framework dependencies

### CLI-Logic Coupling Issues
- Some screens import directly from `database.models` (ORM layer)
- Screen methods contain some business logic (e.g., `_generate_topics` in OpportunitiesScreen)
- Dashboard screen queries database directly instead of through application service

## Future FastAPI Service Boundaries

### 1. Business Service
- `GET /api/businesses` - List businesses
- `POST /api/businesses/discover` - Discover businesses
- `GET /api/businesses/{id}` - Get business details
- `PUT /api/businesses/{id}` - Update business
- `DELETE /api/businesses/{id}` - Delete business
- `POST /api/businesses/{id}/save` - Save business as candidate

### 2. Discovery Service
- `POST /api/discover` - Run discovery with filters
- `GET /api/discover/categories` - Get available categories
- `GET /api/discover/status` - Discovery job status

### 3. Scoring Service
- `POST /api/score/run` - Score all unscored businesses
- `GET /api/score/ranked` - Get ranked candidates
- `GET /api/score/{business_id}` - Get score breakdown

### 4. Website Analysis Service
- `POST /api/website/analyze/{business_id}` - Analyze website
- `GET /api/website/{business_id}` - Get analysis results

### 5. AI Analysis Service
- `POST /api/ai/analyze/{business_id}` - Run AI analysis
- `GET /api/ai/budget` - Get AI usage stats
- `GET /api/ai/{business_id}` - Get AI analysis

### 6. Research Service
- `GET /api/opportunities` - List opportunities
- `POST /api/opportunities/{id}/favorite` - Toggle favorite
- `GET /api/topics` - List topics
- `POST /api/topics` - Create topic
- `PUT /api/topics/{id}` - Update topic
- `POST /api/topics/{id}/save` - Toggle save

### 7. Outreach Service
- `GET /api/outreach` - List outreach
- `POST /api/outreach` - Create draft
- `PUT /api/outreach/{id}` - Update draft
- `POST /api/outreach/{id}/send` - Send email
- `POST /api/outreach/{id}/do-not-contact` - Mark DNC

### 8. Dashboard Service
- `GET /api/dashboard/stats` - Get pipeline stats

### 9. Export Service
- `GET /api/export/csv` - Export businesses CSV
- `GET /api/export/json` - Export all data
- `GET /api/export/markdown` - Export topics markdown

## Authentication Considerations

For future web version:
- JWT-based authentication
- User model for multi-tenant support
- API key management for AI provider
- OAuth2 for email providers (Gmail)

## Background Jobs

- Discovery tasks (queued)
- Website analysis tasks
- AI analysis tasks
- Email sending queue
- Database backup scheduler

## Migration Risks

1. **ORM coupling**: Some screens use SQLAlchemy models directly
2. **Async/sync mixing**: CLI uses asyncio.run() for some operations
3. **State management**: In-memory caches need to be shared across requests
4. **File system dependencies**: Logging and exports use local file system

## Recommended Next Steps

1. Create application services for all screens
2. Add proper dependency injection
3. Create API routers for each service
4. Add authentication middleware
5. Implement background task queue (Celery/RQ)
6. Add rate limiting middleware
7. Create Docker configuration
