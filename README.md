# AutoQA

End-to-end test framework for UI automation and API validation.

| Layer | Tool |
|-------|------|
| Test runner | pytest 8 |
| UI automation | Selenium 4 + webdriver-manager |
| DOM validation | BeautifulSoup4 |
| API testing | requests + Postman collection |
| Reports | pytest-html |
| CI/CD | GitHub Actions |
| Container | Docker |

## Quick start

```bash
pip install -r requirements.txt

# API tests only (no browser needed)
pytest -m api

# UI tests – headless
pytest -m ui --headless

# Smoke suite
pytest -m smoke --headless

# Full run with HTML report → reports/report.html
pytest --headless
```

## Docker

```bash
docker build -t autoqa .
docker run --rm -v "$(pwd)/reports:/app/reports" autoqa
```

## Targets

| Suite | URL |
|-------|-----|
| UI | https://www.saucedemo.com |
| API | https://reqres.in/api |

Override via env vars `BASE_URL` / `API_BASE_URL` or `--base-url` / `--api-base-url` flags.

## Markers

| Marker | Usage |
|--------|-------|
| `smoke` | Fast sanity — runs on every commit |
| `regression` | Full regression suite |
| `ui` | Selenium browser tests |
| `api` | requests-based API tests |
| `slow` | Tests > 10 s |

## Structure

```
pages/       Page Object Model
tests/ui/    Selenium browser tests
tests/api/   requests API tests
tests/regression/  smoke + regression suites
utils/       APIClient wrapper, BeautifulSoup helpers
postman/     Exported Postman collection
reports/     Generated HTML reports (gitignored)
```
