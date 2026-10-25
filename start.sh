#!/bin/bash
# Run this every time:  bash start.sh
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
