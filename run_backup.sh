#!/bin/bash

export $(cat .env | xargs)
python3 mega_backup.py
