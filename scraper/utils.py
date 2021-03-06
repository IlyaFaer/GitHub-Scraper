"""Some utils for tracker."""
import copy
import logging
import shelve
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


def try_match_keywords(body, repo_names):
    """Try to find GitHub keywords in issue's body.

    Args:
        body (str): Issue's body.
        repo_names (tuple): Tracked repositories names.

    Returns:
        list: Key phrases with issue numbers, if found.
    """
    result = []
    if body:
        # check if there are keywords declaring
        # relation to another object in this repo
        for pattern in PATTERNS:
            result += pattern.findall(body)

        # check if there are keywords declaring
        # relation to another object in another
        # repo of this sheet
        for repo_name in repo_names:
            for keyword in ("Closes", "Fixes", "Towards"):
                link = keyword + " " + repo_name + "#"

                if link in body:
                    start_ind = body.index(link)
                    parts = body[start_ind:].split()
                    result += [
                        parts[0] + " " + parts[1],
                    ]
    return result


def log_progress(is_first_update, total, current, message):
    """Log progress of the issues or PRs processing.

    Args:
        is_first_update (bool): This is the first update of this repo.
        total (int): Number of issues/PRs.
        current (int): Last processed issue/PR number.
        message (str): String with the processed object instance.
    """
    if is_first_update and total > 1600:
        if (current + 1) % 400 == 0:
            logging.info(
                "processed {num} of {total} {message}".format(
                    num=current + 1, total=total, message=message
                )
            )


def load_update_stamps(field, sheet_name):
    """Load last issues/PRs update timestamps from the file.

    Args:
        field (str): PRs or issues updates should be loaded.
        sheet_name (str): Name of the sheet.

    Returns:
        dict:
            Index of the last issues/PRs update timestamps
            for every repo on this sheet.
    """
    with shelve.open("last_updates", "c") as lasts_file:
        return lasts_file.setdefault(field, {}).get(sheet_name, {})


def save_update_stamps(field, sheet_name, stamps):
    """Save issues/PRs update timestamps into file for future use.

    Args:
        field (str): Name of the field to save stamps into.
        sheet_name (str): Name of the sheet for which stamps should be saved.
        stamps (dict): Last updates timestamps.
    """
    with shelve.open("last_updates", "w") as lasts_file:
        old_updates = copy.copy(lasts_file[field])
        old_updates[sheet_name] = stamps

        lasts_file[field] = old_updates
