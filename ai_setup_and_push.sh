#!/bin/bash

# Install Python dependencies
pip install openai python-dotenv

# Run the code generator
python code_gen.py

# Commit and push the generated code
git add .
git commit -m "AI Initial Commit"
git push
