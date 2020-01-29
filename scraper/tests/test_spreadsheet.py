"""Unit tests for Spreadsheet class."""
import sys
import examples.fill_funcs_example

sys.modules["fill_funcs"] = examples.fill_funcs_example

import examples.config_example  # noqa: E402

sys.modules["config"] = examples.config_example

import spreadsheet  # noqa: E402
import unittest  # noqa: E402
import unittest.mock as mock  # noqa: E402

SPREADSHEET_ID = "ss_id"


class ConfigMock:
    """Hand-written mock for config module."""

    def __init__(self):
        self.SHEETS = {"sheet1": {}, "sheet2": {}}


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
        self._sheets_ids = {}


CONFIG = ConfigMock()


class TestSpreadsheet(unittest.TestCase):
    """Starting a work with Spreadsheet object."""

    @classmethod
    def setUpClass(self):
        """Init mock for spreadsheet."""
        self._ss_mock = SpreadsheetMock(CONFIG)

    def test_create(self):
        """Init Spreadsheet object with new spreadsheet."""
        with mock.patch(
            "spreadsheet.Spreadsheet._create_spreadsheet", return_value=SPREADSHEET_ID
        ) as create_ss:
            with mock.patch("spreadsheet.CachedSheetsIds") as cache:
                with mock.patch("spreadsheet.Spreadsheet._login_on_google") as login:
                    doc = spreadsheet.Spreadsheet(CONFIG)
                    self.assertEqual(doc._builders, {})
                    self.assertEqual(doc._config, CONFIG)
                    self.assertEqual(doc._columns, [])
                    self.assertEqual(doc._id, SPREADSHEET_ID)

                    login.assert_called_once()

                cache.assert_called_once_with(doc._ss_resource, SPREADSHEET_ID)

            create_ss.assert_called_once()

    def test_init_existing(self):
        """Init Spreadsheet object with existing spreadsheet id."""
        with mock.patch(
            "spreadsheet.Spreadsheet._create_spreadsheet", return_value=SPREADSHEET_ID
        ) as create_ss:
            with mock.patch("spreadsheet.Spreadsheet._login_on_google") as login_mock:
                with mock.patch("spreadsheet.CachedSheetsIds") as cache:
                    doc = spreadsheet.Spreadsheet(CONFIG, SPREADSHEET_ID)
                    self.assertEqual(doc._builders, {})
                    self.assertEqual(doc._config, CONFIG)
                    self.assertEqual(doc._columns, [])
                    self.assertEqual(doc._id, SPREADSHEET_ID)

                    cache.assert_called_once_with(doc._ss_resource, SPREADSHEET_ID)

                login_mock.assert_called_once()

            create_ss.assert_not_called()

    def test_id(self):
        """Check whether id attribute is working fine."""
        ss_mock = SpreadsheetMock(CONFIG, "test_id")
        self.assertEqual(ss_mock._id, ss_mock.id)
        with self.assertRaises(AttributeError):
            ss_mock.id = "new_id"

    def test_new_sheets_requests(self):
        """Check if add-new-sheet requests are built fine."""
        SHEETS_IN_CONF = ("sheet_1", "sheet_2")
        self._ss_mock._sheets_ids = {"sheet_1": True}

        reqs = self._ss_mock._build_new_sheets_requests(SHEETS_IN_CONF)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["addSheet"]["properties"]["title"], "sheet_2")

    def test_delete_sheets_requests(self):
        """Check if delete-sheet requests are built fine."""
        FIRST_SHEET_ID = 123
        SHEETS_IN_CONF = ("sheet_2",)

        with mock.patch.object(
            self._ss_mock,
            "_sheets_ids",
            mock.Mock(as_dict={"sheet_1": FIRST_SHEET_ID, "sheet_2": 456}),
        ):
            reqs = self._ss_mock._build_delete_sheets_requests(SHEETS_IN_CONF)
            self.assertEqual(len(reqs), 1)
            self.assertEqual(reqs[0]["deleteSheet"]["sheetId"], FIRST_SHEET_ID)

    def test_update_all_sheets(self):
        """Update sheets one by one."""
        ss_mock = SpreadsheetMock(CONFIG)
        with mock.patch.object(ss_mock, attribute="update_sheet") as update_sheet:
            ss_mock.update_all_sheets()

            update_sheet.assert_has_calls((mock.call("sheet1"), mock.call("sheet2")))

    def test_reload_config(self):
        """Test reloading the spreadsheet configurations."""
        NEW_SHEETS = {"table1": {}}

        new_config = ConfigMock()
        new_config.SHEETS = NEW_SHEETS

        self._ss_mock.reload_config(new_config)
        self.assertEqual(self._ss_mock._config, new_config)

    def test_apply_formating_data_w_requests(self):
        """Check if batchUpdate() with given requests were called."""
        REQUESTS = [{"req1": {}}]

        execute_mock = mock.Mock()
        batch_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        self._ss_mock._ss_resource = mock.Mock(batchUpdate=batch_mock)
        self._ss_mock._apply_formating_data(REQUESTS)

        batch_mock.assert_called_once_with(
            spreadsheetId=self._ss_mock._id, body={"requests": REQUESTS}
        )

    def test_apply_formating_data_no_requests(self):
        """Check if batchUpdate() haven't been called in case of empty requests."""
        execute_mock = mock.Mock()
        self._ss_mock._ss_resource = mock.Mock(
            batchUpdate=mock.Mock(return_value=mock.Mock(execute=execute_mock))
        )
        self._ss_mock._apply_formating_data([])

        execute_mock.assert_not_called()

    def test_clear_range(self):
        """Check if clear() have been called on a proper range."""
        clear_mock = mock.Mock()
        self._ss_mock._ss_resource = mock.Mock(
            values=mock.Mock(return_value=mock.Mock(clear=clear_mock))
        )
        self._ss_mock._clear_range("sheet_name", 100)

        clear_mock.assert_called_once_with(
            spreadsheetId=self._ss_mock._id, range="sheet_name!102:1000".format()
        )
