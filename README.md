# Research Prospect Finder

A Python CLI tool for discovering established local businesses that may become research/skripsi objects.

## Features

- **Business Discovery** - Search for businesses by location, category, and filters
- **Candidate Scoring** - Deterministic ranking of business suitability
- **Website Analysis** - Public website and online presence analysis
- **AI Analysis** - Optional AI-powered business analysis
- **Research Topics** - Generate and manage research topic candidates
- **Outreach** - Draft and send research participation emails
- **Dashboard** - Overview of your research pipeline

## Installation

```bash
pip install -e .
```

## Usage

```bash
research-finder
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## Development

```bash
pip install -e ".[dev]"
ruff check src/
mypy src/
pytest
```

## Architecture

- `cli/` - CLI interface (presentation layer)
- `application/` - Use cases and orchestration
- `domain/` - Business logic and models
- `providers/` - External service abstractions
- `database/` - SQLAlchemy models and connection
- `services/` - Application services
- `config/` - Configuration and logging
# research-finder
