FROM python:3.10-slim

# Install C++ build tools required by Prophet
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install ML and metrics dependencies
RUN pip install --no-cache-dir prophet pandas requests prometheus-client numpy

COPY src/ml_forecaster.py /app/ml_forecaster.py
WORKDIR /app

CMD ["python", "-u", "ml_forecaster.py"]
