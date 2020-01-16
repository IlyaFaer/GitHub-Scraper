"""
Funtions and objects, which uses Google Sheets API to
build and update issues/PRs tables.
"""
import logging
import string
import sheet_builder
import auth
import fill_funcs
from utils import get_num_from_url
from instances import Columns, Row
from const import DIGITS_PATTERN


logging.basicConfig(
    filename="logs.txt",
    format="[%(levelname)s] %(asctime)s: %(message)s",
    level=logging.INFO,
)

service = auth.authenticate()


class CachedSheetsIds:
    """
    Posts request to get all the sheets of the
    specified spreadsheet, and then keeps their numeric
    ids in the inner dict for future needs.

    Args:
        spreadsheet_id (str):
            Id of a spreadsheet, which sheets must be cached.
    """

    def __init__(self, spreadsheet_id):
        self._sheet_ids = {}
        self._spreadsheet_id = spreadsheet_id

        self.update()

    def update(self):
        """Read sheet ids from the spreadsheet and save them internally."""
        resp = service.spreadsheets().get(spreadsheetId=self._spreadsheet_id).execute()

        for sheet in resp["sheets"]:
            props = sheet["properties"]
            self._sheet_ids[props["title"]] = props["sheetId"]

    def get(self, sheet_name):
        """Get sheet's numeric id by it's name.

        Args:
            sheet_name (str): Name of sheet which id should be returned.

        Returns: numeric id of the given sheet.
        """
        return self._sheet_ids.get(sheet_name)

    @property
    def as_dict(self):
        """Return dict with names and numeric ids of sheets."""
        return self._sheet_ids


class Spreadsheet:
    """Object for reading/updating Google spreadsheet.

    Uses 'config' attr to update spreasheet's structure
    and SheetBuilders to fill sheets with issues/PRs data.

    Args:
        config (module):
            Imported config.py module with all
            spreadsheet preferences.

        id_ (str):
            Id of the existing spreadsheet. If not given,
            new spreadsheet will be created.
    """

    def __init__(self, config, id_=None):
        self._builders = {}  # list of builders for every sheet
        self._config = config
        self._columns = []

        self._id = self._get_or_create(id_)
        self._sheets_ids = CachedSheetsIds(self._id)

    def update_structure(self):
        """Update spreadsheet structure.

        Rename spreadsheet, if name in config.py has been changed.
        Add new sheets into the spreadsheet, delete sheets deleted
        from the configurations.
        """
        try:
            logging.info("updating spreadsheet")
            # spreadsheet rename request
            requests = [
                {
                    "updateSpreadsheetProperties": {
                        "properties": {"title": self._config.TITLE},
                        "fields": "title",
                    }
                }
            ]

            self._sheets_ids.update()
            sheets_in_conf = tuple(self._config.SHEETS.keys())

            # build insert requests for the new sheets
            new_sheets = False
            for sheet_name in sheets_in_conf:
                if not self._sheets_ids.get(sheet_name):
                    new_sheets = True
                    requests.append(
                        {
                            "addSheet": {
                                "properties": {
                                    "title": sheet_name,
                                    "gridProperties": {
                                        "rowCount": 1000,
                                        "columnCount": 26,
                                    },
                                }
                            }
                        }
                    )
            # build delete requests for the sheets, which
            # haven't been found in the configurations
            del_sheets = False
            sheets = self._sheets_ids.as_dict
            for sheet_name in sheets.keys():
                if sheet_name not in sheets_in_conf:
                    del_sheets = True
                    requests.append({"deleteSheet": {"sheetId": sheets[sheet_name]}})

            service.spreadsheets().batchUpdate(
                spreadsheetId=self._id, body={"requests": requests}
            ).execute()

            if new_sheets or del_sheets:
                self._sheets_ids.update()

            logging.info("updated")
        except Exception:
            logging.exception("Exception occured:")

    def update_all_sheets(self):
        """Update all sheets from the configurations one by one."""
        for sheet_name in self._config.SHEETS.keys():
            logging.info("updating " + sheet_name)
            try:
                self.update_sheet(sheet_name)
                logging.info("updated")
            except Exception:
                logging.exception("Exception occured:")

    def update_sheet(self, sheet_name):
        """Update specified sheet with issues/PRs data.

        Args:
            sheet_name (str): Name of the sheet to be updated.
        """
        # build new table from the repositories specified in config.py
        builder = self._builders.setdefault(sheet_name, sheet_builder.SheetBuilder())
        builder.update_config(self._config.SHEETS[sheet_name])
        raw_new_table = builder.build_table()

        tracked_issues = self._read_sheet(sheet_name)

        to_be_deleted = []
        # merging the new table with the old one
        for tracked_id in tracked_issues.keys():
            prs = builder.get_related_prs(tracked_id)
            if tracked_id in raw_new_table:
                updated_issue = raw_new_table.pop(tracked_id)
            else:
                updated_issue = builder.read_issue(*tracked_id)

            if updated_issue:
                # update columns using fill function
                for col in self._columns.names:
                    self._columns.fill_funcs[col](
                        tracked_issues[tracked_id],
                        updated_issue,
                        sheet_name,
                        self._config.SHEETS[sheet_name],
                        prs,
                        False,
                    )

            to_del = fill_funcs.to_be_deleted(
                tracked_issues[tracked_id], updated_issue, prs
            )
            if to_del:
                to_be_deleted.append(tracked_id)

        for id_ in to_be_deleted:
            tracked_issues.pop(id_)

        self._insert_new_issues(tracked_issues, raw_new_table, sheet_name)
        new_table, requests = self._rows_to_lists(tracked_issues.values(), sheet_name)

        self._format_sheet(sheet_name)
        self._insert_into_sheet(sheet_name, new_table, "A2")

        self._clear_range(sheet_name, len(tracked_issues))
        self._apply_formating_data(requests)

    def reload_config(self, config):
        """Load config.py module into spreadsheet object.

        Args:
            config (module):
                Imported config.py module with all preferences.
        """
        self._config = config

    def _get_or_create(self, id_):
        """Return id_ if passed. Create new spreadsheet otherwise.

        Args:
            id_ (str): Spreadsheet id.

        Returns:
            str: spreadsheet id.
        """
        if not id_:
            # creating new spreadsheet with given sheets list
            spreadsheet = (
                service.spreadsheets()
                .create(
                    body={
                        "properties": {"title": self._config.TITLE},
                        "sheets": _gen_sheets_struct(self._config.SHEETS.keys()),
                    }
                )
                .execute()
            )
            id_ = spreadsheet.get("spreadsheetId")
        return id_

    def _clear_range(self, sheet_name, length):
        """Delete data from last cell to the end.

        Args:
            sheet_name (str): Sheet name.
            length (int): Length of issues list.
        """
        sym_range = "{sheet_name}!{start_from}:1000".format(
            sheet_name=sheet_name, start_from=length + 2
        )

        service.spreadsheets().values().clear(
            spreadsheetId=self._id, range=sym_range
        ).execute()

    def _format_sheet(self, sheet_name):
        """Update sheet's structure.

        Create title row in specified sheet, format columns
        and add data validation according to config module.

        Args:
            sheet_name (str): Name of sheet which must be formatted.
        """
        # set validation for team members
        self._config.COLUMNS[7]["values"] = self._config.SHEETS[sheet_name]["team"]

        self._columns = Columns(
            self._config.SHEETS[sheet_name]["columns"], self._sheets_ids.get(sheet_name)
        )

        self._insert_into_sheet(sheet_name, [self._columns.names], "A1")
        self._apply_formating_data(self._columns.requests)

    def _rows_to_lists(self, tracked_issues, sheet_name):
        """Convert every Row into list before sending into spreadsheet.

        Args:
            tracked_issues (list): Rows, each of which represents single row.
            sheet_name (str): Name of sheet to be updated.

        Returns:
            list: Lists, each of which represents single row.
            list: Dicts, each of which represents single coloring request.
        """
        requests = []

        new_table = list(tracked_issues)
        new_table.sort(key=self._config.sort_func)

        # convert rows into lists
        for index, row in enumerate(new_table):
            new_table[index] = row.as_list[: len(self._columns.names)]

            for col, color in row.colors.items():
                requests.append(
                    _gen_color_request(
                        self._sheets_ids.get(sheet_name),
                        index + 1,
                        self._columns.names.index(col),
                        color,
                    )
                )
        return new_table, requests

    def _insert_new_issues(self, tracked_issues, new_issues, sheet_name):
        """Insert new issues into tracked issues index.

        Args:
            tracked_issues (dict): Index of tracked issues.
            new_issues (dict): Index with only recently created issues.
        """
        for new_id in new_issues.keys():
            tracked_issues[new_id] = Row(self._columns.names)
            prs = self._builders[sheet_name].get_related_prs(new_id)

            for col in self._columns.names:
                self._columns.fill_funcs[col](
                    tracked_issues[new_id],
                    new_issues[new_id],
                    sheet_name,
                    self._config.SHEETS[sheet_name],
                    prs,
                    True,
                )

    def _read_sheet(self, sheet_name):
        """
        Read the specified existing sheet and build
        issues index.

        Args:
            sheet_name (str): Name of sheet to be read.

        Returns: Issues index (dict).
        """
        table = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=self._id, range=sheet_name, valueRenderOption="FORMULA")
            .execute()
            .get("values")
        )

        if table is None:
            self._format_sheet(sheet_name)
            table = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._id,
                    range=sheet_name,
                    valueRenderOption="FORMULA",
                )
                .execute()["values"]
            )
        title_row, table = table[0], table[1:]

        _convert_to_rows(title_row, table)
        sheet_id = self._sheets_ids.get(sheet_name)

        self._columns = Columns(self._config.SHEETS[sheet_name]["columns"], sheet_id)
        return _build_index(table, title_row)

    def _insert_into_sheet(self, sheet_name, rows, start_from):
        """Write new data into specified sheet.

        Args:
            sheet_name (str):
                Name of sheet that must be updated.

            rows (list):
                Lists, each of which represents single
                row in a sheet.

            start_from (str):
                Symbolic index, from which data insertion
                must start.
        """
        start_index = int(DIGITS_PATTERN.findall(start_from)[0])

        sym_range = "{start_from}:{last_sym}{count}".format(
            start_from=start_from,
            last_sym=string.ascii_uppercase[len(rows[0]) - 1],
            count=len(rows) + start_index + 1,
        )

        service.spreadsheets().values().update(
            spreadsheetId=self._id,
            range=sheet_name + "!" + sym_range,
            valueInputOption="USER_ENTERED",
            body={"values": rows},
        ).execute()

    def _apply_formating_data(self, requests):
        """Apply formating data with batch update.

        Args:
            requests (list):
                Dicts, each of which represents single request.
        """
        if requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=self._id, body={"requests": requests}
            ).execute()


def _build_index(table, column_names):
    """
    Build dict containing:
    {
        (issue_number, repo_name): Row
    }

    Args:
        table (list): Lists, each of which represents single row.
        column_names (list): Tracked columns names.

    Returns: Dict, which values represents rows.
    """
    index = {}
    for row in table:
        key = (get_num_from_url(row["Issue"]), row["Repository"])
        index[key] = Row(column_names)
        index[key].update(row)
    return index


def _convert_to_rows(title_row, table):
    """Convert every list into Row.

    Args:
        title_row (list): Tracked columns.
        table (list): Lists, eah of which represents single row.
    """
    for index, row in enumerate(table):
        new_row = Row(title_row)
        new_row.fill_from_list(row)
        table[index] = new_row


def _gen_sheets_struct(sheets_config):
    """Build dicts with sheet's preferences.

    Args:
        sheets_config (dict): Sheets preferences.

    Returns:
        List of dicts, each of which represents structure
        for passing into Google Spreadsheet API requests.
    """
    sheets = []

    for sheet_name in sheets_config:
        sheets.append({"properties": {"title": sheet_name}})

    return sheets


def _gen_color_request(sheet_id, row, column, color):
    """Request, that changes color of specified cell."""
    request = {
        "repeatCell": {
            "fields": "userEnteredFormat",
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row,
                "endRowIndex": row + 1,
                "startColumnIndex": column,
                "endColumnIndex": column + 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": color,
                    "horizontalAlignment": "CENTER",
                }
            },
        }
    }
    return request
