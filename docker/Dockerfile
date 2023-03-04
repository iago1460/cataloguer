FROM public.ecr.aws/lambda/python:3.9 AS requirements

ENV POETRY_VIRTUALENVS_CREATE=false \
    INSIDE_DOCKER=true \
    POETRY_VERSION=1.2.1

RUN pip3 install poetry==$POETRY_VERSION

ENV PROJECT_FOLDER=/src

COPY ./pyproject.toml ./poetry.lock ${PROJECT_FOLDER}/
RUN poetry install --no-interaction --no-ansi

COPY ./ ${PROJECT_FOLDER}/

WORKDIR ${PROJECT_FOLDER}
ENV PYTHONUNBUFFERED 1
ENTRYPOINT [ "python3", "-m", "catalogue"]
