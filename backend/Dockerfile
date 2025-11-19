# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from backend
COPY backend/ .

# Expose the port FastAPI will run on
EXPOSE 8000

# Create a startup script that runs migrations then starts the server
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Migrations complete!"\n\
echo "Starting uvicorn server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /start.sh && \
chmod +x /start.sh

# Command to run the startup script
CMD ["/bin/bash", "/start.sh"]