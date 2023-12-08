FROM docker.io/python:3.12.1-alpine3.18

RUN mkdir /app
COPY . /app
RUN cd /app && \
    rm Dockerfile && \
    pip install -r requirements.txt && \
    ./manage.py migrate
WORKDIR /app

ENTRYPOINT ["./manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
    
