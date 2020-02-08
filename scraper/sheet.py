"""API which controls single Google Sheet."""
import sheet_builder
import string
import fill_funcs
from const import DIGITS_PATTERN
from utils import BatchIterator, get_num_from_formula
from instances import Columns, Row


class Sheet:
    """Object related to a single sheet.

    Args:
        name (str): Sheet name.
        spreadsheet_id (str): Parent spreadsheet id.
        id (int): Numeric sheet id.
    """

    def __init__(self, name, spreadsheet_id, id_=None):
        self.id = id_
        self.name = name
        self.ss_id = spreadsheet_id
        self._config = None
        self._builder = None

    @property
    def create_request(self):
        """'Create' request for this sheet.

        Can be used to create real sheet if this object
        was initiated before real sheet creation.

        Returns:
            dict: Request which creates new sheet related to this object.
        """
        request = {
            "addSheet": {
                "properties": {
                    "title": self.name,
                    "gridProperties": {"rowCount": 1000, "columnCount": 26},
                }
            }
        }
        return request

    @property
    def delete_request(self):
        """'Delete' request for this sheet.

        Can be used to delete the real sheet, related to this object.

        Returns:
            dict: Request which removes the real sheet related to this object.
        """
        return {"deleteSheet": {"sheetId": self.id}}

    def reload_config(self, config):
        """Reload sheet configurations.

        Args:
            config (dict): Sheet configurations.
        """
        self._config = config

    def update(self, ss_resource):
        """Update specified sheet with issues/PRs data."""
        self._prepare_builder()

        raw_new_table = self._builder.retrieve_updated()
        tracked_issues = self._read(ss_resource)

        to_be_deleted = []
        # merging the new table into the old one
        for tracked_id in tracked_issues.keys():
            updated_issue = None
            if tracked_id in raw_new_table:
                updated_issue = raw_new_table.pop(tracked_id)
            # on a first update check old (closed issues included)
            # rows too in case of Scraper restarts
            elif self._builder.first_update:
                updated_issue = self._builder.read_issue(*tracked_id)
            # if issue wasn't updated, take it's last
            # version from internal index
            else:
                updated_issue = self._builder.get_from_index(tracked_id)

            prs = self._builder.get_related_prs(tracked_id)
            if updated_issue:
                # update columns using fill function
                for col in self._columns.names:
                    self._columns.fill_funcs[col](
                        tracked_issues[tracked_id],
                        updated_issue,
                        self.name,
                        self._config,
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
            self._builder.delete_from_index(id_)

        self._insert_new_issues(tracked_issues, raw_new_table)
        new_table, requests = self._prepare_table(tracked_issues.values())

        self._format_sheet(ss_resource)
        self._insert(ss_resource, new_table, "A2")

        self._clear_bottom(ss_resource, len(tracked_issues), len(self._columns.names))
        self._post_requests(ss_resource, requests)
        self._builder.first_update = False

    def _prepare_builder(self):
        """Initiate builder for this sheet."""
        if self._builder is None:
            self._builder = sheet_builder.SheetBuilder()

        self._builder.update_config(self._config)

    def _insert(self, ss_resource, rows, start_from):
        """Write new data into this sheet.

        Args:
            rows (list):
                Lists, each of which represents single row.

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

        ss_resource.values().update(
            spreadsheetId=self.ss_id,
            range=self.name + "!" + sym_range,
            valueInputOption="USER_ENTERED",
            body={"values": rows},
        ).execute()

    def _post_requests(self, ss_resource, requests):
        """Post requests with batch update.

        Args:
            requests (list):
                Dicts, each of which represents single request.
        """
        if requests:
            for batch in BatchIterator(requests):
                ss_resource.batchUpdate(
                    spreadsheetId=self.ss_id, body={"requests": batch}
                ).execute()

    def _format_sheet(self, ss_resource):
        """Update sheet structure.

        Create title row in the specified sheet, format columns
        and add data validation according to config module.
        """
        self._columns = Columns(self._config["columns"], self.id)

        self._insert(ss_resource, [self._columns.names], "A1")
        self._post_requests(ss_resource, self._columns.requests)

    def _read(self, ss_resource):
        """
        Read data from this sheet.

        Returns:
            dict: Issues index.
        """
        table = (
            ss_resource.values()
            .get(spreadsheetId=self.ss_id, range=self.name, valueRenderOption="FORMULA")
            .execute()
            .get("values")
        )

        if table is None:
            self._format_sheet(ss_resource)
            table = (
                ss_resource.values()
                .get(
                    spreadsheetId=self.ss_id,
                    range=self.name,
                    valueRenderOption="FORMULA",
                )
                .execute()["values"]
            )
        title_row, table = table[0], table[1:]
        _convert_to_rows(title_row, table)

        self._columns = Columns(self._config["columns"], self.id)
        return _build_index(table, title_row)

    def _clear_bottom(self, ss_resource, length, width):
        """Clear cells from the last actual row till the end.

        Args:
            length (int): Length of issues list.
        """
        sym_range = "{sheet_name}!A{start_from}:{end}".format(
            sheet_name=self.name,
            start_from=length + 2,
            end=string.ascii_uppercase[width - 1],
        )
        ss_resource.values().clear(spreadsheetId=self.ss_id, range=sym_range).execute()

    def _prepare_table(self, tracked_issues):
        """Convert every Row into list.

        Args:
            tracked_issues (list): Rows, each of which represents single row.

        Returns:
            list: Lists, each of which represents single row.
            list: Dicts, each of which represents single coloring request.
        """
        requests = []

        new_table = list(tracked_issues)
        new_table.sort(key=fill_funcs.sort_func)

        # convert rows into lists
        for index, row in enumerate(new_table):
            new_table[index] = row.as_list[: len(self._columns.names)]

            for col, color in row.colors.items():
                requests.append(
                    _gen_color_request(
                        self.id, index + 1, self._columns.names.index(col), color
                    )
                )
        return new_table, requests

    def _insert_new_issues(self, tracked_issues, new_issues):
        """Insert new issues into tracked issues index.

        Args:
            tracked_issues (dict): Index of tracked issues.
            new_issues (dict): Index with only recently created issues.
        """
        for new_id in new_issues.keys():
            tracked_issues[new_id] = Row(self._columns.names)
            prs = self._builder.get_related_prs(new_id)

            for col in self._columns.names:
                self._columns.fill_funcs[col](
                    tracked_issues[new_id],
                    new_issues[new_id],
                    self.name,
                    self._config,
                    prs,
                    True,
                )


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
        key = (get_num_from_formula(row["Issue"]), row["Repository"])
        index[key] = Row(column_names)
        index[key].update(row)
    return index


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
