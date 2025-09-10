# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application that scrapes soccer match data from the Soccerway API and exports it to Excel format. The application fetches matches for specified date ranges and extracts comprehensive match information including scores, statistics, team forms, and betting odds.

## Development Commands

### Environment Setup
- **Virtual environment**: Uses `.venv` directory (already set up with uv)
- **Install dependencies**: `uv sync` or `uv pip install -e .`
- **Python version**: Requires Python >=3.13 (see `.python-version`)

### Running the Application
- **Run main script**: `python main.py` or `uv run python main.py`
- **Direct execution**: The script provides an interactive console interface for date selection

### Dependencies Management
- **Package manager**: Uses `uv` with `pyproject.toml` configuration
- **Add dependency**: `uv add <package-name>`
- **Update dependencies**: `uv sync`

## Architecture

### Core Components

**main.py**: Single-file application with the following key functions:
- `fetch_matches_data()`: HTTP client for Soccerway API calls
- `parse_match_data()`: JSON parser that extracts match details, team statistics, odds
- `save_to_excel()`: Excel export functionality using pandas and openpyxl
- `get_date_input()`: Interactive console interface for date range selection

### Data Flow
1. User selects date range through console interface
2. Application constructs API URL with date parameters
3. HTTP request to Soccerway API with browser-like headers
4. JSON response parsing into structured match data
5. Export to timestamped Excel file

### Data Structure
The application extracts comprehensive match information:
- Tournament details (name, code, continent, season, phase)
- Match metadata (ID, status, datetime, round, elapsed time)
- Team information (home/away names, scores for full-time and half-time)
- Statistics (cards, corners, substitutions)
- Team form (average points per game)
- Betting odds (1X2 from first bookmaker)

### Configuration
- **API Endpoint**: `https://int.soccerway.com/v1/english/matches/soccer/`
- **Headers**: Configured to mimic Firefox browser requests
- **Output**: Excel files with timestamp format `matches_YYYYMMDD_HHMMSS.xlsx`

## Key Features

- Interactive date selection (specific dates, today/yesterday/tomorrow, date ranges)
- Comprehensive match data extraction from nested JSON structure
- Excel export with structured column names in Russian
- Error handling for API requests and data parsing
- Logging configuration for debugging and monitoring

## Development Notes

- Currently the API call is commented out (line 231-233) and uses `data = None` for testing
- The `example.json` file contains sample API response structure for development/testing
- Uses Russian language for column headers and logging messages