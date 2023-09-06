FROM python:alpine AS download
ENV PYTHONUNBUFFERED=1
RUN apk add --update-cache \
    bash \
    curl

WORKDIR /downloads

RUN curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
RUN chmod +x kubectl
RUN cp /downloads/kubectl /usr/local/bin/kubectl
WORKDIR /app
COPY . /app
