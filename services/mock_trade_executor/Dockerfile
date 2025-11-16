FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set Python path to include the project root
ENV PYTHONPATH=/app

# Run the mock trade executor service
CMD ["python", "services/mock_trade_executor/main.py"]
