# Multi-stage build for optimized image size
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY "requirements.txt " .

# Install Python dependencies in a builder stage
FROM base as builder

WORKDIR /app
COPY "requirements.txt " .
RUN pip install --user --no-cache-dir -r "requirements.txt "

# Final production image
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 streamlit_user

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/streamlit_user/.local

# Copy application code
COPY . .

# Set environment variables
ENV PATH=/home/streamlit_user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Change ownership to non-root user
RUN chown -R streamlit_user:streamlit_user /app

# Switch to non-root user
USER streamlit_user

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
CMD ["streamlit", "run", "part5/general.py"]
