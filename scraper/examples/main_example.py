"""Tracker's main program example.

Create your own main.py to use Scraper.
Your main.py will not be Git-tracked.

It creates Google spreadsheet and then updates it at the
specified interval. Before every update tracker reloads
config.py module to get new preferences and filling functions.
"""
import time
import config
from spreadsheet import Spreadsheet


# TODO: set the existing spreadsheet id, or
# None if new spreadsheet wanted to be created
spreadsheet_id = "1Z9QoQ8xUoOtHVUtrtLV6T78J30jvQS4uE0G4AK2Bhkc"
spreadsheet = Spreadsheet(config, spreadsheet_id)

# updating the spreadsheet at the specified period
while True:
    spreadsheet.reload_config(config)
    spreadsheet.update_structure()
    spreadsheet.update_all_sheets()

    time.sleep(config.UPDATE_PERIODICITY)
