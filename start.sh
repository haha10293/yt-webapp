#!/bin/bash

podman build -t downloader ./downloader
podman run -d \
  --name downloader \
  -p 8000:8000 \
  -v ./downloads:/downloads \
  downloader

podman build -t nextjs ./nextjs
podman run -d \
  --name nextjs \
  -p 3000:3000 \
  nextjs