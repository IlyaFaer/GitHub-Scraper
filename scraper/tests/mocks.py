import github  # noqa: E402
from sheet import Sheet  # noqa: E402
from sheet_builder import SheetBuilder  # noqa: E402
import spreadsheet


SPREADSHEET_ID = "ss_id"


class SheetBuilderMock(SheetBuilder):
    def _login_on_github(self):
        return github.Github()


class SheetMock(Sheet):
    def __init__(self, name, spreadsheet_id, id_=None):
        self.id = id_
        self.name = name
        self.ss_id = spreadsheet_id
        self._config = None
        self._builder = SheetBuilderMock()


class ConfigMock:
    """Hand-written mock for config module."""

    def __init__(self):
        self.SHEETS = {"sheet1": {"repo_names": {}}, "sheet2": {}}
        self.TITLE = "MockTitle"
        self.__file__ = 0


class SpreadsheetMock(spreadsheet.Spreadsheet):
    """Hand-written mock for Spreadsheet objects.

    Overrides some methods to exclude backend calls.
    """

    def __init__(self, config, id_=None):
        self._builders = {}
        self._columns = []
        self._config = config
        self._id = SPREADSHEET_ID
        self._last_config_update = -1
        self._ss_resource = None
        self._config_updated = True
