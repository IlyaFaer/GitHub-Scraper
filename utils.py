"""Some utils for tracker."""
from const import NUM_REGEX


def gen_color_request(sheet_id, row, column, color):
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


def get_num_from_url(url):
    """Get issue number from it's URL.

    Args:
        url (str): URL or formula for issue.

    Returns:
        (str): issue number.
    """
    match = NUM_REGEX.search(url)
    if match is not None:
        result = match.group("num").replace('"', "")
    else:
        result = url

    return result
