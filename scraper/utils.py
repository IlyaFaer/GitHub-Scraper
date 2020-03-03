"""Some utils for tracker."""
from reg_exps import NUM_REGEX, PATTERNS


class BatchIterator:
    """Helper for iterating requests in batches.

    Args:
        requests (list): List of requests to iterate.
        size (int): Size of a single one batch.
    """

    def __init__(self, requests, size=20):
        self._requests = requests
        self._size = size
        self._pos = 0

    def __iter__(self):
        return self

    def __next__(self):
        """Return requests batch with given size.

        Returns:
            list: Requests batch.
        """
        batch = self._requests[self._pos : self._pos + self._size]  # noqa: E203
        self._pos += self._size

        if not batch:
            raise StopIteration()

        return batch


def get_num_from_formula(formula):
    """Get issue number from spreadsheet HYPERLINK formula.

    Args:
        formula (str): URL or HYPERLINK formula.

    Returns:
        str: issue number.
    """
    match = NUM_REGEX.search(formula)
    if match is not None:
        return match.group("num").replace('"', "")
    return formula


def get_url_from_formula(formula):
    """Return URL from the given HYPERLINK formula.

    Args:
        formula (str): HYPERLINK formula.

    Returns:
        str: Resource URL.
    """
    return formula.split('",')[0][12:]


def parse_url(url):
    """Return repo full name and issue from the given URL.

    Args:
        url (str): Resource URL.

    Returns:
        (str, str): Repository URL, issue number.
    """
    parts = url.split("/issues/")
    repo_name = parts[0].replace("https://github.com/", "")
    return repo_name, parts[1]


def build_url_formula(issue):
    """Build formula with issue's URL.

    Args:
        issue (github.Issue.Issue): Issue/PR object.

    Returns:
        str: Formula with issue's URL.
    """
    url = '=HYPERLINK("{url}","{num}")'.format(num=issue.number, url=issue.html_url)
    return url


def try_match_keywords(body):
    """Try to find GitHub keywords in issue's body.

    Args:
        body (str): Issue's body.

    Returns:
        list: Key phrases with issue numbers, if found.
    """
    result = []
    if body:
        for pattern in PATTERNS:
            result += pattern.findall(body)
    return result
