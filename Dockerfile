FROM python:3.11.2-slim-buster

RUN pip install poetry==1.4.0

COPY pyproject.toml poetry.lock /project1/

WORKDIR /project1/

RUN poetry install

COPY . /project1/

RUN poetry install

CMD [ "C:\Users\kapli\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311", "-m" ,"project1"]



