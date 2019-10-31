"""
Funtions and objects, which uses Google Sheets API to
build and update issues/PRs tables.
"""
import string
import sheet_builder
import auth
from utils import gen_color_request, get_num_from_url
from instances import Columns, Row
from const import GREY, DIGITS_PATTERN


service = auth.authenticate()


class CachedSheetsIds:
    """
    Class posts request to get all the sheets of specified
    spreadsheet, and then keeps their ids in inner dict
    for future needs.

    Args:
        spreadsheet_id (str):
            Id of a spreadsheet, which sheets must be cached.
    """

    def __init__(self, spreadsheet_id):
        self._sheet_ids = {}
        self._spreadsheet_id = spreadsheet_id

        self.update()

    def update(self):
        """Read sheets and save them internally."""
        resp = service.spreadsheets().get(spreadsheetId=self._spreadsheet_id).execute()

        for sheet in resp["sheets"]:
            props = sheet["properties"]
            self._sheet_ids[props["title"]] = props["sheetId"]

    def get(self, sheet_name):
        """Get sheet's numeric id by it's name.

        Args:
            sheet_name (str): Name of sheet.

        Returns: numeric id of given sheet.
        """
        return self._sheet_ids.get(sheet_name)


class Spreadsheet:
    """Object for reading/updating Google spreadsheet.

    Uses 'config' attr to update spreasheet's structure
    and SheetBuilders to fill sheets with issues/PRs data.

    Args:
        config (module):
            Imported config.py module with all
            spreadsheet preferences.

        id_ (str):
            Id of existing spreadsheet. If not given, new
            spreadsheet will be created.
    """

    def __init__(self, config, id_=None):
        self._builders = {}  # list of builders for every sheet
        self._config = config
        self._columns = []

        if not id_:
            # creating new spreadsheet with given sheets list
            spreadsheet = (
                service.spreadsheets()
                .create(
                    body={
                        "properties": {"title": config.TITLE},
                        "sheets": _gen_sheets_struct(config.SHEETS.keys()),
                    }
                )
                .execute()
            )
            id_ = spreadsheet.get("spreadsheetId")

        self._sheets_ids = CachedSheetsIds(id_)
        self._id = id_

    def update_spreadsheet(self):
        """Update spreadsheet structure.

        Rename spreadsheet, if name in config.py had been changed.
        Add new sheets into spreadsheet.
        """
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

        # build requests for new sheets
        new_sheets = False
        for sheet_name in self._config.SHEETS.keys():
            if not self._sheets_ids.get(sheet_name):
                new_sheets = True
                requests.append(
                    {
                        "addSheet": {
                            "properties": {
                                "title": sheet_name,
                                "gridProperties": {"rowCount": 1000, "columnCount": 26},
                            }
                        }
                    }
                )

        service.spreadsheets().batchUpdate(
            spreadsheetId=self._id, body={"requests": requests}
        ).execute()

        if new_sheets:
            self._sheets_ids.update()

    def update_sheet(self, sheet_name):
        """Update specified sheet with issues/PRs data.

        Args:
            sheet_name (str): Name of sheet to be updated.
        """
        closed_issues = []

        # build new table from repositories
        builder = self._get_sheet_builder(sheet_name)
        builder.update_config(self._config.SHEETS[sheet_name])
        raw_new_table = builder.build_table()

        # read existing data from sheet
        tracked_issues = self._read_sheet(sheet_name)

        # merging new and old tables
        for tracked_id in tracked_issues.keys():
            prs = builder.get_prs(tracked_id)
            if tracked_id in raw_new_table:
                updated_issue = raw_new_table.pop(tracked_id)

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

                closed_issues.append(tracked_issues[tracked_id].as_list)

        self._insert_new_issues(tracked_issues, raw_new_table, sheet_name)
        new_table = self._rows_to_lists(tracked_issues.values())

        requests = builder.fill_prs(new_table)
        self._format_sheet(sheet_name)
        self._insert_into_sheet(sheet_name, new_table, "A2")

        requests += self._gen_closed_requests(closed_issues, new_table, sheet_name)
        self._apply_formating_data(requests)

    def reload_config(self, config):
        """Load config.py module into spreadsheet object.

        Args:
            config (module):
                Imported config.py module with all
                preferences.
        """
        self._config = config

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

    def _rows_to_lists(self, tracked_issues):
        """Convert every Row into list before sending into spreadsheet.

        Args:
            tracked_issues (list): Rows, each of which represents single row.

        Returns:
            list: lists, each of which represents single row.
        """
        new_table = list(tracked_issues)
        new_table.sort(key=self._config.sort_func)

        # convert rows into lists
        for index, row in enumerate(new_table):
            new_table[index] = row.as_list

        return new_table

    def _gen_closed_requests(self, closed_issues, new_table, sheet_name):
        """Generate requests for marking closed issues with color.

        Args:
            closed_issues (list): Issues, that are already closed.

            new_table (list): New data to insert into spreadsheet.

            sheet_name (str): Name of the sheet to be updated.

        Returns:
            list: formatting requests for Google Sheets API.
        """
        requests = []

        for closed_issue in closed_issues:
            num = new_table.index(closed_issue)
            requests.append(
                gen_color_request(self._sheets_ids.get(sheet_name), num + 1, 1, GREY)
            )
        return requests

    def _get_sheet_builder(self, sheet_name):
        """Return builder for specified sheet.

        If builder already created, it'll be taken from
        inner index. Otherwise, it'll be created.

        Args:
            sheet_name (str):
                Name of sheet, for which builder
                must be taken/created.

        Returns: SheetBuilder linked with the given sheet.
        """
        if sheet_name not in self._builders:
            sheet_id = self._sheets_ids.get(sheet_name)
            self._builders[sheet_name] = sheet_builder.SheetBuilder(sheet_id)

        return self._builders[sheet_name]

    def _insert_new_issues(self, tracked_issues, new_issues, sheet_name):
        """Insert new issues into tracked issues index.

        Args:
            tracked_issues (dict): Index of tracked issues.
            new_issues (dict): Index with only recently created issues.
        """
        for new_id in new_issues.keys():
            tracked_issues[new_id] = Row(self._columns.names)
            prs = self._builders[sheet_name].get_prs(new_id)

            for col in self._columns.names:
                self._columns.fill_funcs[col](
                    tracked_issues[new_id],
                    new_issues[new_id],
                    sheet_name,
                    self._config.SHEETS[sheet_name],
                    prs,
                    True,
                )

    def _convert_to_rows(self, title_row, table):
        """Convert every list into Row.

        Args:
            title_row (list): Tracked columns.
            table (list): Lists, eah of which represents single row.
        """
        for index, row in enumerate(table):
            new_row = Row(title_row)
            new_row.fill_from_list(row)
            table[index] = new_row

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

        self._convert_to_rows(title_row, table)
        sheet_id = self._sheets_ids.get(sheet_name)

        self._columns = Columns(self._config.COLUMNS, sheet_id)
        return build_index(table, title_row)

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
            body = {"requests": requests}

            service.spreadsheets().batchUpdate(
                spreadsheetId=self._id, body=body
            ).execute()


def build_index(table, column_names):
    """
    Build dict containing:
    {
        (issue_number, repo_name): Row
    }

    Args:
        column_names (list): Tracked columns names.

    Returns: Dict, which values represents rows.
    """
    index = {}
    for row in table:
        key = (get_num_from_url(row["Issue"]), row["Repository"])
        index[key] = Row(column_names)
        index[key].update(row)
    return index


def _gen_sheets_struct(sheets_config):
    """Build dicts with sheet's preferences.

    Args:
        sheets_config (dict): Sheets preferences.

    Returns: list of dicts, each of which represents
        structure for passing into Google Spreadsheet API
        requests.
    """
    sheets = []

    for sheet_name in sheets_config:
        sheets.append({"properties": {"title": sheet_name}})

    return sheets
