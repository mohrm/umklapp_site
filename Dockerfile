FROM docker.io/python:3.5.10-alpine3.12

RUN mkdir /app
COPY . /app
RUN cd /app && \
    rm Dockerfile && \
    pip install -r requirements.txt && \
    ./manage.py migrate
WORKDIR /app

ENTRYPOINT ["./manage.py", "runserver", "0.0.0.0:8000"]
    
