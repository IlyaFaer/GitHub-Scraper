import datetime
import unittest
from mocks import SheetBuilderMock


class TestSheetBuilder(unittest.TestCase):
    def test_build_filter_not_updated(self):
        """
        Check if filter built correctly in case of no updates
        were made for specified repository.
        """
        builder = SheetBuilderMock()
        builder._last_issue_updates = {"repo1": (datetime.datetime(1, 1, 1), "")}

        self.assertEqual(builder._build_filter("repo1"), {})

    def test_build_filter(self):
        """Check if filter build correctly."""
        DATE_ = datetime.datetime(2020, 6, 3)

        builder = SheetBuilderMock()
        builder._last_issue_updates = {"repo1": (DATE_, "issue_url")}

        self.assertEqual(
            builder._build_filter("repo1"),
            {"sort": "updated", "direction": "desc", "since": DATE_, "state": "all"},
        )

    def test_reload_config(self):
        """Check if configurations reloading working fine."""
        REPOS = ("repo1", "repo2")

        builder = SheetBuilderMock()
        builder.reload_config({"repo_names": REPOS})

        self.assertEqual(builder._repo_names, REPOS)

    def test_get_from_index(self):
        """Test getting issues from index."""
        ISSUE1 = {"Title": "Issue title", "Number": 1}
        URL = "url1"

        builder = SheetBuilderMock()
        builder._issues_index = {URL: ISSUE1}

        self.assertEqual(builder.get_from_index("url"), None)
        self.assertEqual(builder.get_from_index(URL), ISSUE1)

    def test_delete_from_index(self):
        """Check indexed issue deletion."""
        ISSUE1 = {"Title": "Issue title", "Number": 1}
        URL = "url1"

        builder = SheetBuilderMock()
        builder._issues_index = {URL: ISSUE1}

        builder.delete_from_index(URL)
        self.assertNotIn(URL, builder._issues_index.keys())
