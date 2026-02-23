# ── Stage 1: Build the Vite/Phaser frontend ─────────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

# Cache dependency install separately from source copy
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build
# Output lands in /app/frontend/dist


# ── Stage 2: Python backend + pre-built frontend ─────────────────────────────
FROM python:3.12-slim

# Non-root user required by Hugging Face Spaces
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend into a location the backend can serve
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Give the non-root user ownership
RUN chown -R appuser:appuser /app

USER appuser

# Hugging Face Spaces requires port 7860
EXPOSE 7860

# Run from the backend package directory so relative imports resolve correctly
WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
