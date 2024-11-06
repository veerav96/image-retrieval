Installation
==================

To install Papyrus Retrieval, follow these steps:

1.  **Clone the repository**

    .. code-block:: bash

        git clone https://github.com/veerav96/image-retrieval.git

2.  **Install Pre-Requisites**

    Install Mamba and Docker Engine before proceeding:

    - **Mamba**: A faster alternative to Conda for managing environments. Follow the installation instructions at the official Mamba documentation:

      https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html

    - **Docker Engine**: Ensure Docker is installed and running on your machine. Follow the installation steps based on your operating system:

      https://docs.docker.com/engine/install/


3.  **Create development environment**

    .. code-block:: bash

        mamba env create -f environment.yaml

4.  **Local Infrastructure**

    The application uses `docker-compose <https://docs.docker.com/compose/>`_. It installs dependent services and setup the development infrastructure.


    .. code-block:: bash

       cd infra

       docker compose up -d

5)  **Database Schema**

    To initialize and migrate the PostgreSQL schema we use `Alembic <https://alembic.sqlalchemy.org/en/latest/>`_.

    The following has to be run when working on an empty DB or if the DB-schema gets updated:

    .. code-block:: bash

        export PYTHONPATH="src:$PYTHONPATH"

        export $(xargs < .env)

        alembic upgrade head

    To create new revision :

    .. code-block:: bash

        export PYTHONPATH="src:$PYTHONPATH"

        export $(xargs < .env)

        alembic revision --autogenerate -m "Custom migration message"

6)  **Data**

    To bulk insert reference papyrus images into database, run the following :

    Note: Adjust the folder path where images are located.

    .. code-block:: bash

        python -m src.tasks.scheduled_tasks



7)  **Run**

    Before running the application create an `.env` file using the `.env_template`.
    Populate `.env` with relevant configuration

    **Celery**

    Run the background task workers:

    .. code-block:: bash

        export $(xargs < .env)

        export PYTHONPATH="src:$PYTHONPATH"

        celery -A src.tasks.workflow_tasks worker -l INFO &

    **Webapp**

    Run the FastAPI/uvicorn webserver.

    .. code-block:: bash

        export $(xargs < .env)

        export PYTHONPATH="src:$PYTHONPATH"

        python src/main.py &

    Go to `<https://localhost:8000>`_ to see the webpage in action.

    Alternatively go to `<https://localhost:8000/docs>`_ to see the api in action.


    **Inference Server**

    Run the `litserve <https://lightning.ai/docs/litserve/features/gpu-inference>`_ powered inference server.

    .. code-block:: bash

        python -m src.inference.server &

    Go to `<https://localhost:8001/docs>`_ to see the inference api in action.




