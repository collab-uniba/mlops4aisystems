"""Set up the project configuration"""

import configparser
import json
import logging
from datetime import datetime
from pathlib import Path

import pretty_errors
from rich.logging import RichHandler

# Load environment variables from `env.ini`
config = configparser.ConfigParser()
env_file = Path("env.ini")
if not env_file.exists():
    raise ValueError("The env.ini file does not exist.")
else:
    config.read(env_file)

# Load settings from `settings.json`
settings_file = Path("settings.json")
if not settings_file.exists():
    raise ValueError("The settings.json file does not exist.")
else:
    with open(settings_file) as s:
        EXPERIMENT_SETTINGS = json.load(s)

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

# Ensure the dumps directory exists
DUMPS_DIR = Path(config["PATHS"]["DUMPS_DIR"])
DUMPS_DIR.mkdir(parents=True, exist_ok=True)


# ---------- #
# GITHUB API #
# ---------- #

TOKEN_LIST: list[str] = json.loads(config["GITHUB"]["TOKEN_LIST"])
