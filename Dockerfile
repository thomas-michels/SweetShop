FROM python:3.10-alpine

WORKDIR .

COPY ./requirements/prod.txt ./requirements.txt

RUN pip install --upgrade pip \
    && pip install Authlib[Starlette] httpx itsdangerous requests PyJWT \
    && pip install --no-cache -r /requirements.txt

COPY ./app ./app
COPY ./main.py ./main.py

EXPOSE 8080

ENTRYPOINT ["uvicorn"]

CMD ["app.application:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8080"]
