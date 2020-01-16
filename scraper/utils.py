"""Some utils for tracker."""
from const import NUM_REGEX, PATTERNS, YELLOW_RAPS, PINK, PURPLE


def get_num_from_url(url):
    """Get issue number from it's URL.

    Args:
        url (str): URL or formula for issue.

    Returns:
        str: issue number.
    """
    match = NUM_REGEX.search(url)
    if match is not None:
        return match.group("num").replace('"', "")
    return url


def build_url_formula(issue):
    """Build formula with issue's URL.

    Args:
        issue (github.Issue.Issue): Issue/PR object.

    Returns:
        str: formula with issue's URL.
    """
    url = '=HYPERLINK("{url}";"{num}")'.format(num=issue.number, url=issue.html_url)
    return url


def try_match_keywords(body):
    """Try to find keywords in issue's body.

    Args:
        body (str): Issue's body.

    Returns: List of key phrases with issue numbers, if found.
    """
    result = []
    if body:
        for pattern in PATTERNS:
            result += pattern.findall(body)
    return result


def designate_status_color(pull, team):
    """Check PR's status and return corresponding color.

    Args:
        pull (github.PullRequest.PullRequest):
            Pull request object.
    """
    status = None

    if pull.merged:
        status = PURPLE
    elif pull.state == "closed" and not pull.merged:
        status = PINK
    elif pull.user.login not in team:
        status = YELLOW_RAPS

    return status