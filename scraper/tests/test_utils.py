"""Unit tests for scraper utils."""
import unittest
import utils


class TestBatchIterator(unittest.TestCase):
    """Tests for BatchIterator."""

    def test_batch_iterator(self):
        """Check if BatchIterator iteration works fine."""
        REQUESTS = [1, 2, 3, 4, 5, 6, 7, 8]

        b_iter = utils.BatchIterator(REQUESTS, 3)
        self.assertEqual(next(b_iter), [1, 2, 3])
        self.assertEqual(next(b_iter), [4, 5, 6])
        self.assertEqual(next(b_iter), [7, 8])
