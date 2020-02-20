"""Unit tests for Spreadsheet class."""
import sys
import examples.fill_funcs_example

sys.modules["fill_funcs"] = examples.fill_funcs_example

import examples.config_example  # noqa: E402

sys.modules["config"] = examples.config_example
import unittest  # noqa: E402
import unittest.mock as mock  # noqa: E402
from mocks import SheetMock  # noqa: E402


SPREADSHEET_ID = "ss_id"


class TestSheet(unittest.TestCase):
    def test_post_requests_w_no_requests(self):
        """Check if batchUpdate() haven't been called in case of empty requests."""
        sheet = SheetMock("sheet1", SPREADSHEET_ID)

        execute_mock = mock.Mock()
        ss_resource_mock = mock.Mock(
            batchUpdate=mock.Mock(return_value=mock.Mock(execute=execute_mock))
        )
        sheet._post_requests(ss_resource_mock, [])

        execute_mock.assert_not_called()

    def test_post_requests(self):
        """Check if batchUpdate() with given requests were called."""
        REQUESTS = [{"req1": {}}]

        sheet = SheetMock("sheet1", SPREADSHEET_ID)

        execute_mock = mock.Mock()
        batch_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        ss_resource_mock = mock.Mock(batchUpdate=batch_mock)

        sheet._post_requests(ss_resource_mock, REQUESTS)

        batch_mock.assert_called_once_with(
            spreadsheetId=SPREADSHEET_ID, body={"requests": REQUESTS}
        )

    def test_reload_config(self):
        """Check if sheet configurations reloaded correclty."""
        sheet = SheetMock("sheet1", SPREADSHEET_ID)
        CONFIG = {"repo_names": {}}

        with mock.patch(
            "sheet_builder.SheetBuilder.reload_config"
        ) as builder_reload_mock:
            sheet.reload_config(CONFIG)

            builder_reload_mock.assert_called_once_with(CONFIG)

        self.assertEqual(sheet._config, CONFIG)

    def test_clear_bottom(self):
        """Check that clearing table bottom works fine."""
        sheet = SheetMock("sheet1", SPREADSHEET_ID)

        execute_mock = mock.Mock()
        clear_mock = mock.Mock(execute=execute_mock)
        values_mock = mock.Mock(return_value=mock.Mock(clear=clear_mock))
        ss_resource_mock = mock.Mock(values=values_mock)

        sheet._clear_bottom(ss_resource_mock, 5, 10)

        clear_mock.assert_called_once_with(
            spreadsheetId=SPREADSHEET_ID, range="sheet1!A7:J"
        )
