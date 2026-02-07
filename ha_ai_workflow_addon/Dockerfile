# HA AI Gen Workflow Add-on for Home Assistant
# Provides a Streamlit-based GUI for the AI workflow
#
# Build context: ha_ai_workflow_addon/ (set by HA builder --target)
# The workflow stages required files into this directory before building.
#
# Performance notes:
# - Uses --prefer-binary to avoid compiling packages from source when
#   pre-built musllinux wheels are available (saves 10-20+ minutes)
# - Build deps (gcc, cargo, etc.) are installed only if wheel install fails
# - Progress output is enabled so long installs show feedback

ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install runtime system dependencies first (these are always needed)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-wheel \
    git \
    openssh-client \
    sshpass \
    jq

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/bin \
    HA_CONFIG_DIR=/config \
    HA_INSTALL_DIR=/app

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
# requirements.txt is staged into the build context by the CI workflow
#
# Strategy: try pre-built wheels first (fast, ~2-3 min), fall back to
# source compilation only if needed (slow, 15-30 min).
COPY requirements.txt /app/
RUN echo "=== Phase 1: Installing from pre-built wheels ===" \
    && pip3 install \
        --break-system-packages \
        --prefer-binary \
        --timeout=120 \
        --progress-bar on \
        -r requirements.txt \
    && echo "=== All packages installed from wheels ===" \
    || ( \
        echo "=== Phase 2: Wheel install failed, installing build tools ===" \
        && apk add --no-cache \
            gcc \
            musl-dev \
            python3-dev \
            libffi-dev \
            openssl-dev \
            cargo \
        && echo "=== Retrying install with build tools ===" \
        && pip3 install \
            --break-system-packages \
            --timeout=300 \
            --progress-bar on \
            -r requirements.txt \
        && echo "=== Removing build tools ===" \
        && apk del --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
    ) \
    && rm -rf /root/.cache /root/.cargo /tmp/*

# Copy application files (staged into build context by CI workflow)
COPY bin/ /app/bin/
COPY config/ /app/config/
COPY templates/ /app/templates/

# Copy master script and create ha-ai-workflow CLI command
COPY ha_ai_master_script.sh /app/bin/ha_ai_master_script.sh
RUN chmod +x /app/bin/ha_ai_master_script.sh \
    && ln -sf /app/bin/ha_ai_master_script.sh /usr/local/bin/ha-ai-workflow

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
