#!/usr/bin/env bash
# Render build script for Resume Analyzer Backend

set -o errexit  # Exit on error

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!"