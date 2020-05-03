"""Unit tests for Spreadsheet class."""
import sys
import examples.fill_funcs_example

sys.modules["fill_funcs"] = examples.fill_funcs_example

import examples.config_example  # noqa: E402

sys.modules["config"] = examples.config_example
import logging  # noqa: E402
import unittest  # noqa: E402
import unittest.mock as mock  # noqa: E402
from mocks import SheetMock  # noqa: E402


logging.disable(logging.INFO)
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

    def test_spot_issue_object_updated(self):
        """Test spotting issues objects."""
        sheet = SheetMock("sheet1", SPREADSHEET_ID)

        # check when issue was updated
        self.assertEqual(
            sheet._spot_issue_object("123", {"123": "updated_issue"}), "updated_issue"
        )
        # check on first update
        sheet._builder.first_update = True
        read_mock = mock.Mock(return_value="read_issue")

        with mock.patch.object(sheet, "_builder", read_issue=read_mock):
            self.assertEqual(
                sheet._spot_issue_object("123", {"1253": "Issue"}), "read_issue"
            )
        # check when issue wasn't updated
        sheet._builder.first_update = False
        sheet._builder._issues_index = {"123": "index_issue"}

        self.assertEqual(
            sheet._spot_issue_object("123", {"1253": "Issue"}), "index_issue"
        )

    def test_update_no_updated_issues(self):
        """Check if update was breaked in case of no updated issues."""
        sheet = SheetMock("sheet1", SPREADSHEET_ID)

        with mock.patch.object(sheet._builder, "retrieve_updated", return_value={}):
            with mock.patch.object(sheet, "_read") as read_mock:
                sheet.update(None, [])
                read_mock.assert_not_called()
