"""Set up the project configuration"""

import configparser
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Load configuration from config.ini file
config = configparser.ConfigParser()
config_ini = Path("config.ini")
if not config_ini.exists():
    raise ValueError("The config.ini file does not exist.")
else:
    config.read(config_ini)

# ------- #
# LOGGING #
# ------- #

# Ensure the logs directory exists
LOGS_DIR = Path(config["PATHS"]["LOGS_DIR"])
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logfile_path = LOGS_DIR / (current_time + ".log")
logging.basicConfig(
    filename=logfile_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(message)s",
)

# Mirror logging to stdout
console_handler = logging.StreamHandler(sys.stdout)
logging.getLogger().addHandler(console_handler)


# ------------ #
# DATA STORAGE #
# ------------ #

# Ensure the data directory exists
DATA_DIR = Path(config["PATHS"]["DATA_DIR"])
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------- #
# GITHUB API #
# ---------- #

TOKEN_LIST = json.loads(config["GITHUB"]["TOKEN_LIST"])
