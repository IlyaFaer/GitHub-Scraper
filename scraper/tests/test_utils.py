"""Unit tests for scraper utils."""
import logging
import unittest
import utils


logging.disable(logging.INFO)


class IssueMock:
    """Mock for github.Issue.Issue object."""

    def __init__(self):
        self.number = "123"
        self.html_url = "https://github.com/org_name/repo_name/issues/123"


class TestBatchIterator(unittest.TestCase):
    """Tests for BatchIterator."""

    def test_batch_iterator(self):
        """Check if BatchIterator iteration works fine."""
        REQUESTS = [1, 2, 3, 4, 5, 6, 7, 8]

        b_iter = utils.BatchIterator(REQUESTS, 3)
        self.assertEqual(next(b_iter), [1, 2, 3])
        self.assertEqual(next(b_iter), [4, 5, 6])
        self.assertEqual(next(b_iter), [7, 8])


class TestUtilFunctions(unittest.TestCase):
    """Test util functions."""

    def test_get_num_from_formula(self):
        """Check if separating number of formula works fine."""
        NUM = "123"
        num = utils.get_num_from_formula(NUM)
        self.assertEqual(num, NUM)

        num = utils.get_num_from_formula(
            """=HYPERLINK("https://github.com/org_name/repo_name/issues/123","123")"""
        )
        self.assertEqual(num, "123")

    def test_build_url_formula(self):
        """Check if building HYPERLINK formula works correctly."""
        formula = utils.build_url_formula(IssueMock())
        self.assertEqual(
            formula,
            """=HYPERLINK("https://github.com/org_name/repo_name/issues/123";"123")""",
        )

    def test_match_keywords(self):
        """Check matching the GitHub keywords."""
        self.assertEqual(utils.try_match_keywords(""), [])

        result = utils.try_match_keywords("Some text. Closes #135")
        self.assertEqual(result, ["Closes #135"])
