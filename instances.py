"""Instances, that helps to process columns and rows."""


class Columns:
    """Object for column processing and generating requests.

    Args:
        cols (list):
            Dicts, each of which describes single column.

        sheet_id (int): Numeric sheet's id.
    """
    def __init__(self, cols, sheet_id):
        self._sheet_id = sheet_id
        self._requests = []  # formating requests for columns
        self.names = []  # column names in title row

        # generating requests from configuration
        for index, col in enumerate(cols):
            self.names.append(col['name'])

            self._gen_size_request(index, col)
            self._gen_align_request(index, col)
            self._gen_one_of_request(index, col)
            self._gen_color_requests(index, col)
            self._gen_date_type_request(index, col)

    @property
    def requests(self):
        """
        Return all column requests. Title row request
        must be first!
        """
        self._requests.insert(0, self._title_row_request)
        return self._requests

    @property
    def _title_row_request(self):
        """Bolding and aligning title row."""
        request = {
            'repeatCell': {
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': self._sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': len(self.names)
                },
                'cell': {
                    'userEnteredFormat': {
                        'horizontalAlignment': "CENTER",
                        'textFormat': {'bold': True}
                    }
                }
            }
        }
        return request

    def _gen_date_type_request(self, index, col):
        """
        Request to set date format for column, that
        designed to contain dates.
        """
        if col.get('is_date'):
            request = {
                "repeatCell": {
                    "range": {
                        "sheetId": self._sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1000,
                        "startColumnIndex": index,
                        "endColumnIndex": index + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "DATE",
                                "pattern": "dd mmm yyyy"
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat"
                }
            }
            self._requests.append(request)

    def _gen_align_request(self, index, col):
        """Aligning request for column."""
        if 'align' in col.keys():
            request = {
                'repeatCell': {
                    'fields': 'userEnteredFormat',
                    'range': {
                        'sheetId': self._sheet_id,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                        'startColumnIndex': index,
                        'endColumnIndex': index + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'horizontalAlignment': col['align']
                        }
                    }
                }
            }

            self._requests.append(request)

    def _gen_color_requests(self, index, col):
        """Requests to set color for specific values in cell."""
        if 'values' in col.keys() and isinstance(col['values'], dict):
            for value, color in col['values'].items():
                self._requests.append(
                    {
                        'addConditionalFormatRule': {
                            'rule': {
                                'ranges': [{
                                    'sheetId': self._sheet_id,
                                    'startRowIndex': 1,
                                    'endRowIndex': 1000,
                                    'startColumnIndex': index,
                                    'endColumnIndex': index + 1,
                                }],
                                'booleanRule': {
                                    'condition': {
                                        'type': 'TEXT_EQ',
                                        'values': [{
                                            'userEnteredValue':
                                                value
                                        }]
                                    },
                                    'format': {
                                        'backgroundColor': color
                                    }
                                },
                            }
                        }
                    }
                )

    def _gen_size_request(self, index, col):
        """Request to set column's width."""
        if 'width' in col.keys():
            request = {
                "updateDimensionProperties": {
                    "properties": {"pixelSize": col['width']},
                    "fields": "pixelSize",
                    "range": {
                        "sheetId": self._sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": index,
                        "endIndex": index + 1,
                    }
                }
            }

            self._requests.append(request)

    def _gen_one_of_request(self, index, col):
        """Request to set data validation."""
        if 'values' in col.keys():
            if isinstance(col['values'], dict):
                vals = [{'userEnteredValue': key} for key in col['values'].keys()]
            else:
                vals = [{'userEnteredValue': value} for value in col['values']]

            request = {
                "setDataValidation": {
                    "range": {
                        "sheetId": self._sheet_id,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                        'startColumnIndex': index,
                        'endColumnIndex': index + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": vals
                        },
                    "showCustomUi": True,
                    "strict": True
                    }
                }
            }

            self._requests.append(request)


class Row(dict):
    """Dict-like representation of single row."""
    def __init__(self, column_names):
        super().__init__()
        self._column_names = column_names
        for col in column_names:
            self[col] = ''

    @property
    def as_list(self):
        """Return list representation of row."""
        row = []
        if any(tuple(self.values())):
            for name in self._column_names:
                row.append(self[name])
        return row

    def fill_from_list(self, list_):
        """
        Fill dict from list. Connections between fields
        and list elements are designated by columns list.
        """
        for index, name in enumerate(self._column_names):
            if index < len(list_):
                self[name] = list_[index]
            else:
                self[name] = ''
