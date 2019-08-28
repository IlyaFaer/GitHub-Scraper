"""
Funtions and objects, which uses Google Sheets API to
build and update issues/PRs tables.
"""
import string
import re
import sheet_builder
import auth
from utils import gen_color_request, get_num_from_url
from config import TRACKED_FIELDS, TITLE, SHEETS
from instances import Columns, Row
from const import GREY


DIGITS_PATTERN = re.compile(r"[\d*]+")
service = auth.authenticate()


class CachedSheetsIds:
    """
    Class posts request to get all sheets of specified
    spreadsheet, and then keeps sheet's ids in inner dict
    for future needs.

    Args:
        spreadsheet_id (str):
            Id of spreadsheet, which sheets must be cached.
    """

    def __init__(self, spreadsheet_id):
        self._sheet_ids = {}

        resp = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

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

    Uses 'config' args to update spreasheet's structure
    and SheetBuilders to fill sheets with issues/PRs data.

    Args:
        id_ (str):
            Id of existing spreadsheet. If not given, new
            spreadsheet will be created.
    """

    def __init__(self, id_=None):
        self._builders = {}  # list of builders for every sheet

        if not id_:
            # creating new spreadsheet with given sheets list
            spreadsheet = (
                service.spreadsheets()
                .create(
                    body={
                        "properties": {"title": TITLE},
                        "sheets": _gen_sheets_struct(SHEETS.keys()),
                    }
                )
                .execute()
            )
            id_ = spreadsheet.get("spreadsheetId")

        self._sheets_ids = CachedSheetsIds(id_)
        self._id = id_

    def format_sheet(self, sheet_name, cols, config):
        """
        Create title row in specified sheet, format columns
        and add data validation according to 'config' arg.

        Args:
            sheet_name (str):
                Name of sheet which must be formatted.

            cols (list):
                List of dicts, in which columns described.

            config (dict):
                Dict with sheet's configurations.
        """
        # set validation for team members
        cols[7]["values"] = list(config["team"].keys())

        self._columns = Columns(cols, self._sheets_ids.get(sheet_name))

        self._insert_into_sheet(sheet_name, [self._columns.names], "A1")
        self._apply_formating_data(self._columns.requests)

    def update_sheet(self, sheet_name, columns_config, sheets_config):
        """Update specified sheet with issues/PRs data.

        Args:
            sheet_name (str): Name of sheet to be updated.

            columns_config (dict): Columns preferences.

            sheets_config (dict): Sheet's preferences.
        """
        closed_issues = []

        # build new table from repositories
        builder = self._get_sheet_builder(sheet_name)
        builder.update_config(sheets_config)
        issues_list = builder.build_table()

        # read existing data from sheet
        tracked_issues = self._read_sheet(sheet_name)
        is_new_table = len(tracked_issues) == 0
        raw_new_table = build_index(issues_list, self._columns.names[:10])

        link_fields = [
            col["name"] for col in columns_config if col.get("type") == "link"
        ]

        # merging new and old tables
        for tracked_id in tracked_issues.keys():
            # reset URLs, if they became just numbers
            for col in tracked_issues[tracked_id].keys():
                if col in link_fields and tracked_issues[tracked_id][col].isdigit():
                    tracked_issues[tracked_id][col] = builder.build_url(
                        tracked_issues[tracked_id][col], tracked_id[1]
                    )

            # updating tracked columns
            if tracked_id in raw_new_table:
                updated_issue = raw_new_table.pop(tracked_id)
                for col in TRACKED_FIELDS:
                    if updated_issue[col]:
                        tracked_issues[tracked_id][col] = updated_issue[col]
            # if no such issue in new table, than it was closed
            else:
                closed_issues.append(tracked_issues[tracked_id].as_list)
                continue

        self._insert_new_issues(tracked_issues, raw_new_table)

        new_table = list(tracked_issues.values())
        new_table.sort(key=sort_func)

        print("-------------------------------")
        for index, row in enumerate(new_table):
            print(index + 1, row)
            new_table[index] = row.as_list
        print("-------------------------------")

        sheet_id = self._sheets_ids.get(sheet_name)

        requests = []
        requests += builder.fill_prs(new_table, closed_issues)

        if not is_new_table:
            self._insert_blank_rows(sheet_id, new_table, raw_new_table)

        self._insert_into_sheet(sheet_name, new_table, "A2")

        # formating data
        for closed_issue in closed_issues:
            num = new_table.index(closed_issue)
            requests.append(gen_color_request(sheet_id, num + 1, 1, GREY))

        self._apply_formating_data(requests)

    def _get_sheet_builder(self, sheet_name):
        """Return builder for specified sheet.

        If builder already created, it'll be returned from
        inner index. Otherwise, it'll be created.

        Args:
            sheet_name (str):
                Name of sheet, for which builder
                must be returned/created.

        Returns: SheetBuilder linked with the given sheet.
        """
        builder = self._builders.get(sheet_name)
        if builder is None:
            sheet_id = self._sheets_ids.get(sheet_name)
            builder = sheet_builder.SheetBuilder(sheet_name, sheet_id)
            self._builders[sheet_name] = builder

        return builder

    def _insert_blank_rows(self, sheet_id, new_table, new_issues):
        """
        Inserting blank rows to new issue's position,
        to make correct shift of untracked fields.

        Args:
            sheet_id (int): Numeric sheet id.

            new_table (list):
                Lists, each of which represents single row.

            new_issues (dict): Index of new issues
        """
        insert_requests = []
        indexes = []

        # get all new rows indexes
        for id_ in new_issues:
            indexes.append(new_table.index(new_issues[id_].as_list) + 1)

        # generate insert requests
        for index in sorted(indexes, reverse=True):
            insert_requests.append(
                {
                    "insertRange": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": index,
                            "endRowIndex": index + 1,
                        },
                        "shiftDimension": "ROWS",
                    }
                }
            )

        if insert_requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=self._id, body={"requests": insert_requests}
            ).execute()

    def _insert_new_issues(self, tracked_issues, new_issues):
        """Insert new issues into index of tracked issues.

        Args:
            tracked_issues (dict): Index of tracked issues.
            new_issues (dict): Index with only recently created issues.
        """
        for new_id in new_issues.keys():
            tracked_issues[new_id] = new_issues[new_id]
            tracked_issues[new_id]["Priority"] = "New"

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
            .get(spreadsheetId=self._id, range=sheet_name)
            .execute()["values"]
        )

        title_row = table[0]
        cols_list = [{"name": col} for col in title_row]

        table = table[1:]
        self._convert_to_rows(title_row[:10], table)

        sheet_id = self._sheets_ids.get(sheet_name)
        self._columns = Columns(cols_list, sheet_id)
        return build_index(table, title_row[:10])

    def _insert_into_sheet(self, sheet_name, rows, start_from):
        """Write new data into specified sheet.

        Args:
            sheet_name (str):
                Name of sheet that must be updated.

            rows (list):
                Lists, each of which represents single
                row in a sheet.

            start_from (str):
                Symbolic index, from which data inserting
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
        column_names (list): List of tracked columns names.

    Returns: Dict, which values represents rows.
    """
    index = {}
    for row in table:
        key = (get_num_from_url(row["Issue"]), row["Repository"])
        index[key] = Row(column_names)
        index[key].update(row)
    return index


def sort_func(row):
    """Function that sorts data in table.

    Args:
        row (dict): Dict representation of single row.
    """
    return row["Repository"], row["Project"], int(get_num_from_url(row["Issue"]))


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
