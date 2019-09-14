"""Tracker's main program.

It creates Google spreadsheet according to a structure
described in config.py file, and then updates it at
specified interval. Before every update tracker reloads
config.py module to get new preferences.
"""
import time
import importlib
import logging
import config
from spreadsheet import Spreadsheet


logging.basicConfig(
    filename="logs.txt",
    format="[%(levelname)s] %(asctime)s: %(message)s",
    level=logging.INFO,
)

# spreadsheet_id = None
spreadsheet_id = "1Z9QoQ8xUoOtHVUtrtLV6T78J30jvQS4uE0G4AK2Bhkc"
spreadsheet = Spreadsheet(config, spreadsheet_id)

# updating table at specified period
# if exception raised, log it and continue
while True:
    importlib.reload(config)
    spreadsheet.reload_config(config)

    for sheet_name in config.SHEETS.keys():
        logging.info("updating " + sheet_name)
        spreadsheet.format_sheet(sheet_name)

        try:
            spreadsheet.update_sheet(sheet_name)
            logging.info("updated")
        except Exception:
            logging.exception("Exception occured:")

    time.sleep(config.UPDATE_PERIODICITY)
