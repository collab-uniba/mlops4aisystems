"""Set up the project configuration"""

import configparser
import json
import logging
from datetime import datetime
from pathlib import Path

import pretty_errors
from rich.logging import RichHandler

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
console_handler = RichHandler(markup=True)
logging.getLogger().addHandler(console_handler)

# Configure error formatter
pretty_errors.configure(
    separator_character="*",
    filename_display=pretty_errors.FILENAME_EXTENDED,
    line_number_first=True,
    display_link=True,
    lines_before=5,
    lines_after=2,
    line_color=pretty_errors.RED + "> " + pretty_errors.default_config.line_color,
    code_color="  " + pretty_errors.default_config.line_color,
    truncate_code=True,
    display_locals=True,
)

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
