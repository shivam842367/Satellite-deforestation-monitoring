#!/usr/bin/env bash
set -e

apt-get update
apt-get install -y \
  gdal-bin \
  libgdal-dev \
  libproj-dev \
  proj-data \
  proj-bin

pip install --upgrade pip
pip install -r requirements.txt
