#!/bin/bash
cd "$(dirname "$0")"

docker build -t frontend:latest -f ./DockerfileServer .
docker run -v "$(dirname "$(pwd)"):/repo" -p 80:8050 frontend
