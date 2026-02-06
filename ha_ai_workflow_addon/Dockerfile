# HA AI Gen Workflow Add-on for Home Assistant
# Provides a Streamlit-based GUI for the AI workflow
#
# Build context: ha_ai_workflow_addon/ (set by HA builder --target)
# The workflow stages required files into this directory before building.

ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies and build tools in one layer
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-wheel \
    git \
    openssh-client \
    sshpass \
    jq \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/bin

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
# requirements.txt is staged into the build context by the CI workflow
COPY requirements.txt /app/
RUN for i in 1 2 3 4 5; do \
        pip3 install --no-cache-dir --break-system-packages --timeout=300 -r requirements.txt && break || sleep 15; \
    done || \
    pip3 install --no-cache-dir --break-system-packages --timeout=300 --index-url=https://pypi.org/simple -r requirements.txt

# Remove build dependencies to reduce image size
RUN apk del --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
    && rm -rf /root/.cache /root/.cargo /tmp/*

# Copy application files (staged into build context by CI workflow)
COPY bin/ /app/bin/
COPY config/ /app/config/
COPY templates/ /app/templates/

# Copy add-on run script (lives in the build context natively)
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Create necessary directories
RUN mkdir -p /data /config

# Labels are set dynamically by HA builder from config.yaml
LABEL \
    io.hass.name="HA AI Gen Workflow" \
    io.hass.description="AI-powered Home Assistant configuration workflow" \
    io.hass.type="addon" \
    maintainer="Balkonsen"

# Run the add-on
CMD ["/run.sh"]
