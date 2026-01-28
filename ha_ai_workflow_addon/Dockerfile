# HA AI Gen Workflow Add-on for Home Assistant
# Provides a Streamlit-based GUI for the AI workflow

ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies (Alpine packages)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-wheel \
    git \
    openssh-client \
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
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application files
COPY bin/ /app/bin/
COPY config/ /app/config/
COPY templates/ /app/templates/

# Copy add-on specific files
COPY ha_ai_workflow_addon/run.sh /run.sh
RUN chmod +x /run.sh

# Create necessary directories
RUN mkdir -p /data /config

# Labels
LABEL \
    io.hass.name="HA AI Gen Workflow" \
    io.hass.description="AI-powered Home Assistant configuration workflow" \
    io.hass.type="addon" \
    io.hass.version="1.0.0" \
    maintainer="Balkonsen"

# Run the add-on
CMD ["/run.sh"]
