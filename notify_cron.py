#!/usr/bin/env python3
"""PythonAnywhere Scheduled Task entry point for WeatherTomBot notifications."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import features
import bot

# bot.py configures the feature pack with the real weather and Telegram functions.
result = features.daily_notification_job()
print(f"WeatherTomBot notifications: sent={result}")
