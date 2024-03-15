FROM python:3.11

COPY ./pyproject.toml ./poetry.lock* /

# Install poetry and dependencies
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Set the working directory and copy your application code
WORKDIR /code
COPY ./rag /code/rag

CMD ["poetry", "run", "uvicorn", "rag.app:app", "--host", "0.0.0.0", "--port", "80", "--reload"]