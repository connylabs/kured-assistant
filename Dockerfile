FROM alpine AS download
RUN apk add --update-cache curl
WORKDIR /downloads
RUN curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
RUN chmod +x kubectl

FROM gcr.io/distroless/python3
COPY --from=download /downloads/kubectl /usr/local/bin/kubectl
WORKDIR /app
COPY . /app
ENV PYTHONUNBUFFERED=1
