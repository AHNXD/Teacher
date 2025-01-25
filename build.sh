#!/bin/bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y libzbar0

# Install Python dependencies
pip install -r requirements.txt