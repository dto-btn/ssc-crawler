FROM python:3.10-slim

ENV TZ="Canada/Eastern"

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY crawler.py .

CMD ["python", "./crawler.py"]