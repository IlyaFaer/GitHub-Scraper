"""Unit tests for Spreadsheet class."""
import sys
import examples.fill_funcs_example

sys.modules["fill_funcs"] = examples.fill_funcs_example

import examples.config_example  # noqa: E402

sys.modules["config"] = examples.config_example

from sheet import Sheet  # noqa: E402
import sheet_builder  # noqa: E402
import unittest  # noqa: E402
import unittest.mock as mock  # noqa: E402


SPREADSHEET_ID = "ss_id"


class TestSheet(unittest.TestCase):
    def test_prepare_builder(self):
        """Check if new builder created and used on a next call."""
        sheet = Sheet("sheet1", SPREADSHEET_ID)
        sheet._config = {"repo_names": {}}

        with mock.patch("sheet_builder.SheetBuilder._login_on_github"):
            builder = sheet._prepare_builder()

        self.assertIsInstance(sheet._builder, sheet_builder.SheetBuilder)

        builder2 = sheet._prepare_builder()
        self.assertEqual(builder, builder2)

    def test_post_requests_w_no_requests(self):
        """Check if batchUpdate() haven't been called in case of empty requests."""
        sheet = Sheet("sheet1", SPREADSHEET_ID)

        execute_mock = mock.Mock()
        ss_resource_mock = mock.Mock(
            batchUpdate=mock.Mock(return_value=mock.Mock(execute=execute_mock))
        )
        sheet._post_requests(ss_resource_mock, [])

        execute_mock.assert_not_called()

    def test_post_requests(self):
        """Check if batchUpdate() with given requests were called."""
        REQUESTS = [{"req1": {}}]

        sheet = Sheet("sheet1", SPREADSHEET_ID)

        execute_mock = mock.Mock()
        batch_mock = mock.Mock(return_value=mock.Mock(execute=execute_mock))
        ss_resource_mock = mock.Mock(batchUpdate=batch_mock)

        sheet._post_requests(ss_resource_mock, REQUESTS)

        batch_mock.assert_called_once_with(
            spreadsheetId=SPREADSHEET_ID, body={"requests": REQUESTS}
        )
