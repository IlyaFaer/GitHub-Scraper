"""Tracker's main program.

It updates spreadsheet every hour sheet by sheet.
Uses the document structure described in config.py file.
"""
import datetime
import time
import traceback
import importlib
import config
from sheet import Spreadsheet
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
            spreadsheet.update_sheet(sheet_name, config.SHEETS[sheet_name])
            print(str(datetime.datetime.now()) + ': updated')
        except Exception:
            traceback.print_exc()

    time.sleep(HOUR_DURATION)
