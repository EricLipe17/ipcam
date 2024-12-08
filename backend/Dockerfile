FROM python:3.13.0-slim-bookworm
WORKDIR /backend

COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

ENV PYTHONPATH=/backend

RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN chown -R appuser:appgroup /backend

EXPOSE 8000

COPY . ./

CMD [ "python", "./app/main.py" ]
