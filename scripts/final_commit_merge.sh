#!/bin/bash

echo "Running final checks..."
python3 scripts/diagnostic_report.py

echo "Committing all changes..."
git add .
git commit -m "Final full system build"
git pull origin main --rebase
git push origin main

echo "System ready for deployment."
