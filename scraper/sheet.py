"""API which controls single Google Sheet."""
import string
import fill_funcs
import sheet_builder
from reg_exps import DIGITS_PATTERN
from instances import Columns, Row
from utils import BatchIterator, get_url_from_formula


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
        self._builder = sheet_builder.SheetBuilder(name)

    @property
    def create_request(self):
        """'Create' request for this sheet.

        Can be used to create real sheet, if this object
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
        self._builder.reload_config(config)

    def update(self, ss_resource):
        """Update specified sheet with issues/PRs data."""
        updated_issues = self._builder.retrieve_updated()
        if not updated_issues:
            return

        tracked_issues = self._read(ss_resource)
        self._merge_tables(tracked_issues, updated_issues)

        self._insert_new_issues(tracked_issues, updated_issues)
        new_table, requests = self._prepare_table(tracked_issues.values())

        self._format(ss_resource)
        self._insert(ss_resource, new_table, "A2")

        self._clear_bottom(ss_resource, len(tracked_issues), len(self._columns.names))
        self._post_requests(ss_resource, requests)
        self._builder.first_update = False

    def _merge_tables(self, tracked_issues, updated_issues):
        """Merged new data into the old table.

        Args:
            tracked_issues (dict): Issues loaded from the table.
            updated_issues (dict): Recently update issues.
        """
        to_be_deleted = []

        for issue_id in tracked_issues.keys():
            issue_obj = self._spot_issue_object(issue_id, updated_issues)

            prs = self._builder.get_related_prs(issue_id)
            if issue_obj:
                # update columns using fill function
                for col in self._columns.names:
                    self._columns.fill_funcs[col](
                        tracked_issues[issue_id],
                        issue_obj,
                        self.name,
                        self._config,
                        prs,
                        False,
                    )

                to_del = fill_funcs.to_be_deleted(
                    tracked_issues[issue_id], issue_obj, prs
                )
                if to_del:
                    to_be_deleted.append(issue_id)

        for id_ in to_be_deleted:
            tracked_issues.pop(id_)
            self._builder.delete_from_index(id_)

    def _spot_issue_object(self, id_, updated_issues):
        """Designate issue object.

        Args:
            id_ (str): Issue URL.
            updated_issues (dict): Dict of issues updated after the last filling.

        Returns:
            (github.Issue.Issue): Issue object.
        """
        # issue was update
        if id_ in updated_issues.keys():
            return updated_issues.pop(id_)
        # issue closed, but it's the first update after start
        elif self._builder.first_update:
            return self._builder.read_issue(id_)
        # issue wasn't updated, and it's not the first update
        # after start - take issue object from index
        else:
            return self._builder.get_from_index(id_)

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
        """Post requests with batchUpdate().

        Args:
            requests (list):
                Dicts, each of which represents single request.
        """
        if requests:
            for batch in BatchIterator(requests):
                ss_resource.batchUpdate(
                    spreadsheetId=self.ss_id, body={"requests": batch}
                ).execute()

    def _format(self, ss_resource):
        """Update sheet structure.

        Create title row in the specified sheet, format columns
        and add data validation according to config module.
        """
        self._columns = Columns(self._config["columns"], self.id)

        self._insert(ss_resource, [self._columns.names], "A1")
        self._post_requests(ss_resource, self._columns.requests)

    def _read(self, ss_resource):
        """Read data from this sheet.

        Returns:
            dict: Issues index.
        """
        table = (
            ss_resource.values()
            .get(spreadsheetId=self.ss_id, range=self.name, valueRenderOption="FORMULA")
            .execute()
            .get("values")
        )

        if table is None:  # sheet is completely clear
            self._format(ss_resource)
            table = (
                ss_resource.values()
                .get(
                    spreadsheetId=self.ss_id,
                    range=self.name,
                    valueRenderOption="FORMULA",
                )
                .execute()["values"]
            )

        self._columns = Columns(self._config["columns"], self.id)
        return _build_index(table[1:], table[0])

    def _clear_bottom(self, ss_resource, length, width):
        """Clear cells from the last actual row till the end.

        Args:
            length (int): Length of issues list.
            width (int): Number of columns in range to clear.
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
        new_table = list(tracked_issues)
        new_table.sort(key=fill_funcs.sort_func)
        requests = []

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
            if fill_funcs.to_be_ignored(new_issues[new_id]):
                continue

            tracked_issues[new_id] = Row(self._columns.names)

            for col in self._columns.names:
                self._columns.fill_funcs[col](
                    tracked_issues[new_id],
                    new_issues[new_id],
                    self.name,
                    self._config,
                    self._builder.get_related_prs(new_id),
                    True,
                )


def _build_index(table, column_names):
    """
    Build dict containing:
    {
        <issue HTML URL>: Row
    }

    Args:
        table (list): Lists, each of which represents single row.
        column_names (list): Tracked columns names.

    Returns:
        dict: Index of Rows.
    """
    issues_index = {}
    for list_ in table:
        row = Row(column_names)
        row.fill_from_list(list_)

        issues_index[get_url_from_formula(row["Issue"])] = row
    return issues_index


def _gen_color_request(sheet_id, row, column, color):
    """Request to change color of the specified cell.

    Args:
        sheet_id (int): Numeric sheet id.
        row (int): Number of the row to highlight with color.
        column (int): Number of the column to highlight with color.
        color (str): Color code.

    Returns:
        dict: Highlighting request.
    """
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
