# SiteScore

SiteScore is a Streamlit-based retail location intelligence app for Gujarat, India. It scores retail sites on demand potential, footfall proxies, competition, accessibility, catchment quality, and generates a PDF report.

## Features

- Streamlit dashboard for single-site scoring
- Google Maps address search and location selection
- Site scoring using Google Places, OSM, and census-derived proxies
- Benchmark comparison for restaurant, pharmacy, supermarket, bank, and school sites
- Session history and PDF report generation

## Requirements

- Python 3.11+ recommended
- `GOOGLE_API_KEY` environment variable for Google Maps and Places APIs

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/gohilmilansinh/sitescore-app.git
   cd sitescore-app
   ```

2. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Set your Google API key:

   ```bash
   export GOOGLE_API_KEY="your_api_key_here"
   ```

4. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

## Usage

- Open the app in your browser when Streamlit launches.
- Select a site type and search for an address in Gujarat.
- Click `Score This Site` to generate a score and report.
- Use the `History` mode to review past site scores within your browser session.

## Notes

- The current validation logic is centered on Gujarat cities such as Ahmedabad, Surat, Vadodara, and Rajkot.
- The scoring engine uses a mix of Google Places data, OSM data, and hard-coded census proxy data.
- The project currently does not include automated tests, but CI is configured to validate Python source files.

## Project Structure

- `app.py` — Streamlit UI and interaction flow
- `scorer.py` — geocoding and scoring functions
- `report.py` — PDF report generation
- `history.py` — session-based history storage
- `benchmarks.py` — benchmark location data and context helpers
- `census_data.py` — census-based population scoring helpers
- `requirements.txt` — Python dependencies
- `requirements-dev.txt` — development and test dependencies

## Development

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

Run formatting and lint checks with pre-commit:

```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

If you want to improve the app, consider adding:

- unit tests for scoring and benchmark logic
- better error handling for Google API failures
- wider geographic coverage and data sources
- deployment instructions or Docker support
