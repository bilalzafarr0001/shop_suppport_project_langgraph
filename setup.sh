#!/bin/bash
# Run this ONE time:  bash setup.sh
cd "$(dirname "$0")"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env
open -e .env
echo "Paste your Groq key in the .env file, save it, then run:  bash start.sh"
