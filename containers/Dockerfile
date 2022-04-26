FROM python:3.8

WORKDIR /app

# Install Python packages from pypi
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Install local utils
COPY pyproject.toml pyproject.toml
COPY setup.cfg setup.cfg
COPY src src
RUN pip install .

# Copy over the dummy trainer
COPY trainer trainer

ENTRYPOINT [ "python", "-m", "trainer.task"]