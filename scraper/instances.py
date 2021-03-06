"""Instances, that helps to process columns and rows."""
import string
from fill_funcs import dont_fill


class Columns:
    """Object for column processing and generating requests.

    Args:
        cols (list):
            Dicts, each of which describes single column.

        sheet_id (int): Numeric sheet id.
    """

    def __init__(self, cols, sheet_id):
        self._sheet_id = sheet_id
        self._requests = []  # formating requests for columns
        self.names = []  # column names in title row
        self.fill_funcs = {}

        # generating requests from configuration
        for index, col in enumerate(cols):
            self.names.append(col["name"])

            self._gen_size_request(index, col)
            self._gen_align_request(index, col)
            self._gen_one_of_request(index, col)
            self._gen_color_request(index, col)
            self._gen_date_type_request(index, col)

            self.fill_funcs[col["name"]] = col.get("fill_func", dont_fill)

    @property
    def requests(self):
        """
        Return all column requests. Title row request
        must be the first one!

        Returns:
            list: Columns formatting requests.
        """
        self._requests.insert(0, self._title_row_request)
        return self._requests

    def column_symbol(self, column):
        """Return columns letter.

        Args:
            column (str): Column name.

        Returns:
            str: Letter coordinate of the column.
        """
        return string.ascii_uppercase[self.names.index(column)]

    @property
    def _title_row_request(self):
        """Bolding and aligning title row.

        Returns:
            dict: Title row formatting request.
        """
        request = {
            "repeatCell": {
                "fields": "userEnteredFormat",
                "range": {
                    "sheetId": self._sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(self.names),
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True},
                    }
                },
            }
        }
        return request

    def _gen_date_type_request(self, index, col):
        """
        Request to set date format for column, that
        designed to contain dates.

        Args:
            index (int): Column index.
            col (dict): Column configurations.
        """
        if col.get("type") == "date":
            request = {
                "repeatCell": {
                    "range": {
                        "sheetId": self._sheet_id,
                        "startColumnIndex": index,
                        "endColumnIndex": index + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "DATE", "pattern": "dd mmm yyyy"}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
            self._requests.append(request)

    def _gen_align_request(self, index, col):
        """Aligning request for column.

        Args:
            index (int): Column index.
            col (dict): Column description.
        """
        if "align" in col.keys():
            request = {
                "repeatCell": {
                    "fields": "userEnteredFormat",
                    "range": {
                        "sheetId": self._sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": index,
                        "endColumnIndex": index + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {"horizontalAlignment": col["align"]}
                    },
                }
            }

            self._requests.append(request)

    def _gen_color_request(self, index, col):
        """Requests to set color for specific values in cell.

        Args:
            index (int): Column index.
            col (dict): Column description.
        """
        if "values" in col.keys() and isinstance(col["values"], dict):
            for value, color in col["values"].items():
                self._requests.append(
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [
                                    {
                                        "sheetId": self._sheet_id,
                                        "startRowIndex": 1,
                                        "startColumnIndex": index,
                                        "endColumnIndex": index + 1,
                                    }
                                ],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": value}],
                                    },
                                    "format": {"backgroundColor": color},
                                },
                            }
                        }
                    }
                )

    def _gen_size_request(self, index, col):
        """Request to set column's width.

        Args:
            index (int): Column index.
            col (dict): Column description.
        """
        if "width" in col.keys():
            request = {
                "updateDimensionProperties": {
                    "properties": {"pixelSize": col["width"]},
                    "fields": "pixelSize",
                    "range": {
                        "sheetId": self._sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": index,
                        "endIndex": index + 1,
                    },
                }
            }

            self._requests.append(request)

    def _gen_one_of_request(self, index, col):
        """Request to set data validation.

        Args:
            index (int): Column index.
            col (dict): Column description.
        """
        if "values" in col.keys():
            if isinstance(col["values"], dict):
                vals = [{"userEnteredValue": key} for key in col["values"].keys()]
            else:
                vals = [{"userEnteredValue": value} for value in col["values"]]

            request = {
                "setDataValidation": {
                    "range": {
                        "sheetId": self._sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": index,
                        "endColumnIndex": index + 1,
                    },
                    "rule": {
                        "condition": {"type": "ONE_OF_LIST", "values": vals},
                        "showCustomUi": True,
                        "strict": True,
                    },
                }
            }

            self._requests.append(request)


class Row(dict):
    """Dict-like representation of a single row.

    Args:
        column_names (list): List of column names.
    """

    def __init__(self, column_names):
        super().__init__()
        # fill this dict for coloring cells in manner:
        # {col_name: color}
        self.colors = {}

        self._column_names = column_names
        for col in column_names:
            self[col] = ""

    def as_list(self, columns=None):
        """Return list representation of this row.

        Columns can be set with columns arg. Otherwise
        list of columns will be taken from the row itself.

        Args:
            columns (Columns):
                Object to designate columns and their
                order while conversion into list().

        Returns:
            list: List prepared for insertion into sheet.
        """
        row = []
        col_names = columns.names if columns is not None else self._column_names
        if any(self.values()):
            for name in col_names:
                row.append(self[name])
        return row

    def fill_from_list(self, list_):
        """
        Fill this Row from the given list. Relations between
        fields and list elements are designated by columns list.

        Args:
            list_ (list): List representation of the row.
        """
        for index, name in enumerate(self._column_names):
            if index < len(list_):
                self[name] = list_[index]
            else:
                self[name] = ""
