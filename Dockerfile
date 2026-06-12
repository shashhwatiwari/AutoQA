# ---------------------------------------------------------------------------
# AutoQA — portable test runner image
#
# Build:  docker build -t autoqa .
# Run all tests:
#         docker run --rm -v "$(pwd)/reports:/app/reports" autoqa
# Run by marker:
#         docker run --rm -v "$(pwd)/reports:/app/reports" autoqa -m smoke
#         docker run --rm -v "$(pwd)/reports:/app/reports" autoqa -m "api" -n auto
#         docker run --rm -v "$(pwd)/reports:/app/reports" autoqa -m regression
#
# Reports land in ./reports/ on the host via the volume mount.
# ---------------------------------------------------------------------------

FROM python:3.11-slim AS base

LABEL org.opencontainers.image.title="AutoQA"
LABEL org.opencontainers.image.description="Selenium + requests QA automation suite"
LABEL org.opencontainers.image.source="https://github.com/shashwat-tiwari/AutoQA"

# ---------------------------------------------------------------------------
# System dependencies required by Chromium/Chrome
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    unzip \
    # Audio / display stubs (needed even in headless mode)
    fonts-liberation \
    libasound2 \
    # ATK accessibility
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    # Printing / CUPS
    libcups2 \
    # D-Bus
    libdbus-1-3 \
    # DRM / GPU (software renderer fallback)
    libdrm2 \
    libgbm1 \
    # GTK
    libgtk-3-0 \
    # NSS / NSPR (TLS)
    libnspr4 \
    libnss3 \
    # Wayland / X11
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Install Google Chrome stable
# Using the official .deb — webdriver-manager will match the correct driver.
# ---------------------------------------------------------------------------
RUN wget -q -O /tmp/chrome.deb \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/* \
    && google-chrome --version

# ---------------------------------------------------------------------------
# Python dependencies (separate layer — only rebuilds when requirements change)
# ---------------------------------------------------------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Application source
# (.dockerignore excludes .venv, __pycache__, reports, .git)
# ---------------------------------------------------------------------------
COPY . .

# Pre-create the reports directory so pytest-html never fails on a missing path
RUN mkdir -p reports

# ---------------------------------------------------------------------------
# Runtime environment
# CI=true  → conftest.py enables headless Chrome automatically
# No additional --headless flag needed; conftest detects CI.
# PYTHONUNBUFFERED → streaming log output in docker logs / CI
# ---------------------------------------------------------------------------
ENV CI=true \
    PYTHONUNBUFFERED=1 \
    # Chrome flags required inside a container (no sandbox, no /dev/shm limit)
    CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu"

# ---------------------------------------------------------------------------
# Entrypoint — every docker run argument is appended to pytest.
#
# Examples:
#   docker run --rm autoqa                          # all tests
#   docker run --rm autoqa -m smoke                 # smoke only
#   docker run --rm autoqa -m api -n auto           # parallel API tests
#   docker run --rm autoqa --co -q                  # collect/list only
# ---------------------------------------------------------------------------
ENTRYPOINT ["pytest"]
CMD ["--headless", "-v", "--tb=short"]
