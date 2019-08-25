"""Tracker's main program.

It creates Google spreadsheet according to a structure
described in config.py file, and then updates it every
hour. Before every update tracker reloads structure
from config.py to get new preferences.
"""
import datetime
import time
import traceback
import importlib
import config
from spreadsheet import Spreadsheet
from const import HOUR_DURATION


# spreadsheet_id = None
spreadsheet_id = '1Z9QoQ8xUoOtHVUtrtLV6T78J30jvQS4uE0G4AK2Bhkc'

spreadsheet = Spreadsheet(spreadsheet_id)

# updating table every hour
# if exception raised, print it's message and continue
while True:
    importlib.reload(config)

    for sheet_name in config.SHEETS.keys():
        print(str(
            datetime.datetime.now()
        ) + ': updating ' + sheet_name)

        spreadsheet.format_sheet(
            sheet_name,
            config.COLUMNS,
            config.SHEETS[sheet_name]
        )

        try:
            spreadsheet.update_sheet(
                sheet_name,
                config.COLUMNS,
                config.SHEETS[sheet_name]
            )
            print(str(datetime.datetime.now()) + ': updated')
        except Exception:
            traceback.print_exc()

    time.sleep(HOUR_DURATION)
