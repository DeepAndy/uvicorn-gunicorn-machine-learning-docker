import time

import docker
import pytest
import requests

from ..utils import CONTAINER_NAME, get_config, get_logs, remove_previous_container

client = docker.from_env()


def verify_container(container, response_text):
    config_data = get_config(container)
    assert config_data["workers_per_core"] == 2
    assert config_data["host"] == "0.0.0.0"
    assert config_data["port"] == "8000"
    assert config_data["loglevel"] == "warning"
    assert config_data["bind"] == "0.0.0.0:8000"
    logs = get_logs(container)
    assert "Checking for script in /app/prestart.sh" in logs
    assert "Running script /app/prestart.sh" in logs
    assert (
        "Running inside /app/prestart.sh, you could add migrations to this file" in logs
    )
    response = requests.get("http://127.0.0.1:8000")
    assert response.text == response_text


@pytest.mark.parametrize(
    "image,response_text",
    [
        (
            "tiangolo/uvicorn-gunicorn-machine-learning:latest",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "tiangolo/uvicorn-gunicorn-machine-learning:python3.6",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.6",
        ),
        (
            "tiangolo/uvicorn-gunicorn-machine-learning:python3.7",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.7",
        ),
        (
            "tiangolo/uvicorn-gunicorn-machine-learning:python3.6-tensorflow",
            "Hello world! From Uvicorn with Gunicorn. Using Python 3.6",
        ),
    ],
)
def test_env_vars_1(image, response_text):
    remove_previous_container(client)
    container = client.containers.run(
        image,
        name=CONTAINER_NAME,
        environment={"WORKERS_PER_CORE": 2, "PORT": "8000", "LOG_LEVEL": "warning"},
        ports={"8000": "8000"},
        detach=True,
    )
    time.sleep(1)
    verify_container(container, response_text)
    container.stop()
    # Test that everything works after restarting too
    container.start()
    time.sleep(1)
    verify_container(container, response_text)
    container.stop()
    container.remove()
