FROM python:3.11.2-slim-buster

RUN pip install poetry==1.4.0

COPY pyproject.toml poetry.lock /project1/

WORKDIR /project1/

RUN poetry config virtualenvs.create false

RUN poetry install

COPY . /project1/

RUN poetry install

CMD ["uvicorn", "--host", "0.0.0.0", "project1.app:app"]
