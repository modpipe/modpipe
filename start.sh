#!/usr/bin/env bash
if [ ! -d /data/venv ]; then
	python -m venv /data/venv
fi

if [ ! -f /data/venv/bin/activate ]; then
	python -m venv /data/venv
fi

source /data/venv/bin/activate
pip install -r requirements.txt

flask --app modpipe.py run -h 0.0.0.0 --debug
