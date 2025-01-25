#!/bin/bash
# Install system dependencies
apt-get update
apt-get install -y libzbar0

# Install Python dependencies
pip install -r requirements.txt