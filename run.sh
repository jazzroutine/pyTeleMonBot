#!/bin/bash
# Shell wrapper script to activate virtual environment
# Used in /etc/systemd/system/pyTeleMonBot.service

source /opt/pyTeleMonBot/.venv/bin/activate
python3 /opt/pyTeleMonBot/main.py