"""Some utils for scraper."""

def gen_color_request(sheet_id, row, column, color):
    """Request, that changes color of specified cell."""
    request = {
        'repeatCell': {
            'fields': 'userEnteredFormat',
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': row,
                'endRowIndex': row + 1,
                'startColumnIndex': column,
                'endColumnIndex': column + 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': color,
                    'horizontalAlignment': "CENTER",
                }
            }
        }
    }
    return request


def get_num_from_url(url):
    """Get issue number from it's URL."""
    if 'https://' in url:
        result = url.split(';')[1][1:-2]
    else:
        result = url

    return result
