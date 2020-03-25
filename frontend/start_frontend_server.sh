#!/bin/bash
cd "$(dirname "$0")"

cp -R /etc/letsencrypt/live/causality-vs-corona.de .
docker build -t frontend:latest -f ./DockerfileServer .
docker run -v "/etc/letsencrypt:/letsencrypt" -v "$(dirname "$(pwd)"):/repo" -p 8050:8050 frontend
