FROM python:3.9.12-slim-buster

WORKDIR /app

# Install Python packages from pypi
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Install local utils
COPY pyproject.toml pyproject.toml
COPY setup.cfg setup.cfg
ADD src /app/src
RUN pip install .