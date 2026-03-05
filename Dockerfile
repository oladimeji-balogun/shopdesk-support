FROM python:3.10-slim 

WORKDIR /shopdesk-support

COPY requirements.txt . 

RUN pip install --default-timeout=300 --no-cache-dir -r requirements.txt 

COPY . . 

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]