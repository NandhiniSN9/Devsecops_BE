# Stage 1: Build
FROM python:3.13-slim AS build

WORKDIR /app

# Install build dependencies + wkhtmltopdf requirements
RUN apt-get update && apt-get install -y \
    wget gcc libpq-dev \
    fontconfig libfreetype6 libjpeg62-turbo libpng16-16 \
    libx11-6 libxcb1 libxext6 libxrender1 \
    xfonts-75dpi xfonts-base \
    && rm -rf /var/lib/apt/lists/*

# Install libssl1.1 (required by wkhtmltopdf)
RUN wget http://security.debian.org/debian-security/pool/updates/main/o/openssl/libssl1.1_1.1.1n-0+deb10u6_amd64.deb \
    && dpkg -i libssl1.1_1.1.1n-0+deb10u6_amd64.deb \
    && rm libssl1.1_1.1.1n-0+deb10u6_amd64.deb

# Install wkhtmltopdf (patched Qt - full CSS3 support)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb \
    && rm wkhtmltox_0.12.6-1.buster_amd64.deb

# Install uv and Python dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml ./
RUN uv sync --no-dev


# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Copy Python packages and wkhtmltopdf from build
COPY --from=build /app/.venv /app/.venv
COPY --from=build /usr/local/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
COPY --from=build /usr/local/lib/libwkhtmltox* /usr/local/lib/
COPY --from=build /usr/lib/x86_64-linux-gnu/libssl.so.1.1 /usr/lib/x86_64-linux-gnu/
COPY --from=build /usr/lib/x86_64-linux-gnu/libcrypto.so.1.1 /usr/lib/x86_64-linux-gnu/

# Install runtime libs (fonts + shared libs for wkhtmltopdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core fonts-liberation libfontconfig1 \
    libfreetype6 libjpeg62-turbo libpng16-16 \
    libx11-6 libxcb1 libxext6 libxrender1 \
    xfonts-75dpi xfonts-base libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Install uv for running the app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy application code
COPY pyproject.toml main.py ./
COPY src/ ./src/
COPY api/ ./api/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
