#!/bin/bash

echo "Running tidy-up..."
black .
prettier --write .
flake8 .
eslint .

echo "Adding changes..."
git add .

echo "Committing..."
git commit -m "Tidy-up and formatting"

echo "Pushing to main..."
git push origin main

echo "Done! Codebase tidied and pushed."
