"""Unit tests for Spreadsheet class."""
import sys
import examples.fill_funcs_example

sys.modules["fill_funcs"] = examples.fill_funcs_example

import examples.config_example  # noqa: E402

sys.modules["config"] = examples.config_example

import spreadsheet  # noqa: E402
from sheet import Sheet  # noqa: E402
import unittest  # noqa: E402
import unittest.mock as mock  # noqa: E402

SPREADSHEET_ID = "ss_id"


class ConfigMock:
    """Hand-written mock for config module."""

    def __init__(self):
        self.SHEETS = {"sheet1": {"repo_names": {}}, "sheet2": {}}
        self.TITLE = "MockTitle"


class SpreadsheetMock(spreadsheet.Spreadsheet):
    """Hand-written mock for Spreadsheet objects.

    Overrides some methods to exclude backend calls.
    """

    def __init__(self, config, id_=None):
        self._builders = {}
        self._columns = []
        self._config = config
        self._id = SPREADSHEET_ID
        self._ss_resource = None


CONFIG = ConfigMock()


class TestSpreadsheet(unittest.TestCase):
    """Starting a work with Spreadsheet object."""

    @classmethod
    def setUpClass(self):
        """Init mock for spreadsheet."""
        self._ss_mock = SpreadsheetMock(CONFIG)

    def test_init_create(self):
        """Init Spreadsheet object with mew spreadsheet creation."""
        SS_RESOURCE = "SS_RESOURCE"
        SHEETS = "SHEETS"

        with mock.patch("auth.authenticate", return_value=SS_RESOURCE) as auth_mock:
            with mock.patch(
                "spreadsheet.Spreadsheet._create", return_value=SPREADSHEET_ID
            ) as create_mock:
                with mock.patch(
                    "spreadsheet.Spreadsheet._init_sheets", return_value=SHEETS
                ) as init_sheets_mock:
                    doc = spreadsheet.Spreadsheet(CONFIG)

                    init_sheets_mock.assert_called_once()
                create_mock.assert_called_once()
            auth_mock.assert_called_once()

        self.assertEqual(doc._config, CONFIG)
        self.assertEqual(doc._id, SPREADSHEET_ID)
        self.assertEqual(doc._ss_resource, SS_RESOURCE)
        self.assertEqual(doc.sheets, SHEETS)

    def test_init_existing(self):
        """Init Spreadsheet object with existing spreadsheet id."""
        SS_RESOURCE = "SS_RESOURCE"
        SHEETS = "SHEETS"

        execute_mock = mock.Mock()
        batch_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        self._ss_mock._ss_resource = mock.Mock(batchUpdate=batch_mock)

        with mock.patch("auth.authenticate", return_value=SS_RESOURCE) as auth_mock:
            with mock.patch(
                "spreadsheet.Spreadsheet._create", return_value=SPREADSHEET_ID
            ) as create_ss:
                with mock.patch(
                    "spreadsheet.Spreadsheet._init_sheets", return_value=SHEETS
                ) as init_sheets_mock:
                    doc = spreadsheet.Spreadsheet(CONFIG, SPREADSHEET_ID)
                    init_sheets_mock.assert_called_once()
                create_ss.assert_not_called()
            auth_mock.assert_called_once()

        self.assertEqual(doc._config, CONFIG)
        self.assertEqual(doc._id, SPREADSHEET_ID)
        self.assertEqual(doc._ss_resource, SS_RESOURCE)
        self.assertEqual(doc.sheets, SHEETS)

    def test_id(self):
        """Check whether id attribute is working fine."""
        ss_mock = SpreadsheetMock(CONFIG, "test_id")
        self.assertEqual(ss_mock._id, ss_mock.id)
        with self.assertRaises(AttributeError):
            ss_mock.id = "new_id"

    def test_update_structure_no_update(self):
        """
        Test spreadsheet structure updating without
        sheet creation and deletion.
        """
        RENAME_REQUEST = {
            "updateSpreadsheetProperties": {
                "properties": {"title": "MockTitle"},
                "fields": "title",
            }
        }

        execute_mock = mock.Mock()
        batch_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        self._ss_mock._ss_resource = mock.Mock(batchUpdate=batch_mock)

        with mock.patch("spreadsheet.Spreadsheet._actualize_sheets") as actual_mock:
            self._ss_mock.update_structure()
            actual_mock.assert_not_called()

        batch_mock.assert_called_once_with(
            body={"requests": [RENAME_REQUEST]}, spreadsheetId="ss_id"
        )

    def test_update_structure(self):
        """
        Test spreadsheet structure updating.
        New sheet creation and old sheet deleting included.
        """
        SHEET3_ID = 5623
        RENAME_REQUEST = {
            "updateSpreadsheetProperties": {
                "properties": {"title": "MockTitle"},
                "fields": "title",
            }
        }
        CREATE_REQUEST = {
            "addSheet": {
                "properties": {
                    "title": "sheet1",
                    "gridProperties": {"rowCount": 1000, "columnCount": 26},
                }
            }
        }
        DELETE_REQUEST = {"deleteSheet": {"sheetId": SHEET3_ID}}

        ss_mock = SpreadsheetMock(CONFIG, "test_id")
        ss_mock.sheets = {
            "sheet2": Sheet("sheet2", SPREADSHEET_ID, 123),
            "sheet3": Sheet("sheet3", SPREADSHEET_ID, SHEET3_ID),
        }
        execute_mock = mock.Mock()
        batch_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        ss_mock._ss_resource = mock.Mock(batchUpdate=batch_mock)

        with mock.patch("spreadsheet.Spreadsheet._actualize_sheets") as actual_mock:
            ss_mock.update_structure()
            actual_mock.assert_called_once()

        batch_mock.assert_called_once_with(
            body={"requests": [RENAME_REQUEST, CREATE_REQUEST, DELETE_REQUEST]},
            spreadsheetId="ss_id",
        )

    def test_update_all_sheets(self):
        """Update sheets one by one."""
        ss_mock = SpreadsheetMock(CONFIG)
        sheet1 = Sheet("sheet1", SPREADSHEET_ID)
        sheet2 = Sheet("sheet2", SPREADSHEET_ID)

        ss_mock.sheets = {"sheet1": sheet1, "sheet2": sheet2}
        with mock.patch("sheet.Sheet.update") as update_sheet:
            ss_mock.update_all_sheets()

            # no spreadsheet resource used in
            # this test, so args will be None
            update_sheet.assert_has_calls((mock.call(None), mock.call(None)))

    def test_reload_config(self):
        """Test reloading the spreadsheet configurations."""
        NEW_SHEETS = {"sheet1": {}, "sheet2": {}}

        new_config = ConfigMock()
        new_config.SHEETS = NEW_SHEETS

        self._ss_mock.sheets = {
            "sheet1": Sheet("sheet1", SPREADSHEET_ID),
            "sheet2": Sheet("sheet2", SPREADSHEET_ID),
        }

        self._ss_mock.reload_config(new_config)
        self.assertEqual(self._ss_mock._config, new_config)

    def test_init_sheets(self):
        SHEET1 = "sheet1"
        SHEET2 = "sheet2"
        SHEET1_ID = 6345345
        SHEET2_ID = 1456241

        execute_mock = mock.Mock(
            return_value={
                "sheets": [
                    {"properties": {"title": SHEET1, "sheetId": SHEET1_ID}},
                    {"properties": {"title": SHEET2, "sheetId": SHEET2_ID}},
                ]
            }
        )
        get_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))

        ss_mock = SpreadsheetMock(CONFIG)
        ss_mock._ss_resource = mock.Mock(get=get_mock)

        sheets = ss_mock._init_sheets()
        self.assertEqual(sheets[SHEET1].id, SHEET1_ID)
        self.assertEqual(sheets[SHEET1].name, SHEET1)

        self.assertEqual(sheets[SHEET2].id, SHEET2_ID)
        self.assertEqual(sheets[SHEET2].name, SHEET2)

    def test_actualize_sheets(self):
        SHEET1 = "sheet1"
        SHEET2 = "sheet2"
        SHEET2_ID = 1456241

        ss_mock = SpreadsheetMock(CONFIG)
        ss_mock.sheets = {
            SHEET1: Sheet(SHEET1, SPREADSHEET_ID),
            SHEET2: Sheet(SHEET2, SPREADSHEET_ID),
        }

        execute_mock = mock.Mock(
            return_value={
                "sheets": [{"properties": {"title": SHEET2, "sheetId": SHEET2_ID}}]
            }
        )
        get_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        ss_mock._ss_resource = mock.Mock(get=get_mock)

        ss_mock._actualize_sheets()
        self.assertIsNone(ss_mock.sheets.get(SHEET1))
        self.assertEqual(ss_mock.sheets[SHEET2].id, SHEET2_ID)

    def test_new_sheets_requests(self):
        """Check if add-new-sheet requests are built fine."""
        SHEETS_IN_CONF = ("sheet_1", "sheet_2")
        self._ss_mock.sheets = {"sheet_1": Sheet("sheet_1", SPREADSHEET_ID)}

        reqs = self._ss_mock._build_new_sheets_requests(SHEETS_IN_CONF)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["addSheet"]["properties"]["title"], "sheet_2")

    def test_delete_sheets_requests(self):
        """Check if delete-sheet requests are built fine."""
        FIRST_SHEET_ID = 123
        SHEETS_IN_CONF = ("sheet_2",)
        self._ss_mock.sheets = {
            "sheet_1": Sheet("sheet_1", SPREADSHEET_ID, FIRST_SHEET_ID),
            "sheet_2": Sheet("sheet_2", SPREADSHEET_ID),
        }

        reqs = self._ss_mock._build_delete_sheets_requests(SHEETS_IN_CONF)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["deleteSheet"]["sheetId"], FIRST_SHEET_ID)

    def test_create(self):
        ss_mock = SpreadsheetMock(CONFIG)

        execute_mock = mock.Mock(get=mock.Mock(return_value=SPREADSHEET_ID))
        create_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        ss_mock._ss_resource = mock.Mock(create=create_mock)

        ss_mock._create()
        create_mock.assert_called_once_with(
            body={
                "properties": {"title": "MockTitle"},
                "sheets": [
                    {"properties": {"title": "sheet1"}},
                    {"properties": {"title": "sheet2"}},
                ],
            }
        )
