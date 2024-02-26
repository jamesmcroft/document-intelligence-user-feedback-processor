FROM mcr.microsoft.com/vscode/devcontainers/python:1-3.12-bullseye

COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends poppler-utils tesseract-ocr libtesseract-dev ffmpeg libsm6 libxext6 python3-opencv
