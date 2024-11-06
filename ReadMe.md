This code is written for a software practical course at Heidelberg University.

# Papyrus Retrieval

## Documentation

The full documentation for this project is hosted on [Read the Docs](https://image-retrieval.readthedocs.io/).

![Documentation Status](https://readthedocs.org/projects/image-retrieval/badge/?version=latest)

# Introduction

This project is an end-to-end image retrieval webapp! Our main goal is to retrieve similar papyrus images. This can be thought of as 'Google Lens' for papyrus images. The result is a hyperlink to the most similar papyrus, and the corresponding metadata and information about it can be found on [papyri.info](https://papyri.info/).


![Problem Statement](src/docs/assets/intro1.jpeg)
*Alt text: problem statement*

## Demo

Use the installation guide to set up the project and download the data for the demo. Once the installation is successful, the webapp can be launched.

![Demo GIF](src/docs/assets/demo.gif)
*Alt text: demo gif*


## Installation

To install **Papyrus Retrieval**, follow these steps:

1. **Clone the repository**

    ```bash
    git clone https://github.com/veerav96/image-retrieval.git
    ```

2. **Install Pre-Requisites**

    Install **Mamba** and **Docker Engine** before proceeding:

    - **Mamba**: A faster alternative to Conda for managing environments. Follow the installation instructions at the official Mamba documentation:

      [Mamba Installation Guide](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)

    - **Docker Engine**: Ensure Docker is installed and running on your machine. Follow the installation steps based on your operating system:

      [Docker Installation Guide](https://docs.docker.com/engine/install/)

3. **Create the development environment**

    ```bash
    mamba env create -f environment.yaml
    ```

4. **Local Infrastructure**

    The application uses **docker-compose**. It installs dependent services and sets up the development infrastructure.

    ```bash
    cd infra
    docker compose up -d
    ```

5. **Database Schema**

    To initialize and migrate the PostgreSQL schema, we use [Alembic](https://alembic.sqlalchemy.org/en/latest/).

    The following commands need to be run when working on an empty DB or if the DB schema gets updated:

    ```bash
    export PYTHONPATH="src:$PYTHONPATH"
    export $(xargs < .env)
    alembic upgrade head
    ```

    To create a new revision:

    ```bash
    export PYTHONPATH="src:$PYTHONPATH"
    export $(xargs < .env)
    alembic revision --autogenerate -m "Custom migration message"
    ```

6. **Data**

    To bulk insert reference papyrus images into the database, run the following command (adjust the folder path where images are located):

    ```bash
    python -m src.tasks.scheduled_tasks
    ```

7. **Run**

    Before running the application, create an `.env` file using the `.env_template`. Populate the `.env` file with relevant configuration.

    **Celery**: Run the background task workers:

    ```bash
    export $(xargs < .env)
    export PYTHONPATH="src:$PYTHONPATH"
    celery -A src.tasks.workflow_tasks worker -l INFO &
    ```

    **Webapp**: Run the FastAPI/uvicorn webserver:

    ```bash
    export $(xargs < .env)
    export PYTHONPATH="src:$PYTHONPATH"
    python src/main.py &
    ```

    Go to `https://localhost:8000` to see the webpage in action. Alternatively, go to `https://localhost:8000/docs` to see the API in action.

    **Inference Server**: Run the [litserve](https://lightning.ai/docs/litserve/features/gpu-inference) powered inference server:

    ```bash
    python -m src.inference.server &
    ```

    Go to `https://localhost:8001/docs` to see the inference API in action.

