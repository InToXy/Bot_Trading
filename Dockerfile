FROM python:3.11-slim

WORKDIR /app/Project_trading

COPY . /app

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt
    
ENV PYTHONPATH=/app/Project_trading

CMD ["python", "trading/tradingbot.py"]
