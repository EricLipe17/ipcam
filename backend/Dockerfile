FROM python:3.13.0-slim-bookworm
WORKDIR /backend

RUN apt-get update && apt-get install gcc libpq-dev ffmpeg libsm6 libxext6  -y

ENV PYTHONPATH=/backend

RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN chown -R appuser:appgroup /backend

EXPOSE 8000

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./

CMD [ "python", "./app/main.py" ]
