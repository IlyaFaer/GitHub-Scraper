"""
Filling functions example. Create and tweak your own
fill_funcs.py. Your fill_funcs.py will not be Git-tracked.

Functions, which are used for filling columns in
a single one row.

Every filling function accepts:

old_issue (Row): Dict-like object, which represents
row, retrieved from the spreadsheet. Redact its values to
update row in the spreadsheet. Use its colors attribute
for coloring cells.

issue (github.Issue.Issue): Issue object, read from GitHub.

sheet_name (str): Target sheet name.

sheet_config (dict): Sheet configurations from config.py.

prs (list): List of related pull requests (designated by
GitHub keywords). Pull requests are sorted by creation
date (DESC).

is_new (bool): New issue in the table.
"""
import datetime
from utils import build_url_formula, get_num_from_formula


def fill_priority(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Priority' column filling."""
    if is_new:
        old_issue["Priority"] = "New"
        return

    if old_issue["Priority"] in ("Closed", "Done"):
        return

    labels = [label.name for label in issue.labels]

    if "backend" in labels:
        old_issue["Priority"] = "Low"

    elif "help wanted" in labels:
        old_issue["Priority"] = "High"

    elif old_issue["Priority"] == "New":
        # if issue have been new for three or more days,
        # designate its priority
        date_diff = datetime.date.today() - issue.created_at.date()

        if date_diff.days > 3:
            our_labels = []

            for our_label in (
                "api: storage",
                "api: spanner",
                "api: firestore",
                "api: datastore",
                "api: bigtable",
                "api: pubsub",
                "api: core",
            ):
                if our_label in labels:
                    our_labels.append(our_label)

            if our_labels:
                # bugs are prioritized
                if "type: bug" in labels:
                    old_issue["Priority"] = "High"
                # other issues
                else:
                    old_issue["Priority"] = "Medium"
            # other projects
            else:
                old_issue["Priority"] = "Low"


def fill_issue(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Issue' column filling.

    Closed issue number will be colored by grey.
    """
    if is_new:
        old_issue["Issue"] = build_url_formula(issue)

    if issue.closed_at:
        old_issue.colors["Issue"] = {"red": 0.6, "green": 0.6, "blue": 0.6}


def fill_status(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Work status' column filling."""
    if is_new:
        old_issue["Work status"] = "Pending"


def fill_created(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Created' column filling."""
    old_issue["Created"] = issue.created_at.strftime("%d %b %Y")


def fill_description(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Description' column filling."""
    old_issue["Description"] = issue.title


def fill_assignee(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Assignee' column filling."""
    if issue.assignees:
        for assignee in issue.assignees:
            if assignee.login in sheet_config["columns"][7]["values"]:
                old_issue["Assignee"] = assignee.login
                return

        old_issue["Assignee"] = "Other"
    else:
        old_issue["Assignee"] = "N/A"


def fill_repository(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Repository' column filling."""
    if is_new:
        old_issue["Repository"] = sheet_config["repo_names"][issue.repository.full_name]


def fill_project(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Project' column filling."""
    projects = set()

    for label in issue.labels:
        if "api:" in label.name:
            project = sheet_config["labels"].get(label.name, "Other")
            projects.add(project)

    projects = list(projects)
    projects.sort()
    old_issue["Project"] = ", ".join(projects)


def fill_ppr(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Public PR' column filling."""
    if prs:
        old_issue["Public PR"] = build_url_formula(prs[0])

        old_issue.colors["Public PR"] = _designate_status_color(
            prs[0], sheet_config["columns"][7]["values"]
        )


def dont_fill(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """
    Dummy fill function, default for columns
    with no filling function defined.
    """
    pass


def to_be_deleted(row, issue, prs):
    """
    Cleanup function, which designates if issue should be
    deleted from the spreadsheet.

    Args:
        row (Row):
            Dict-like object, which represents
            row, retrieved from the spreadsheet.
        issue (github.Issue.Issue): Issue object, read from GitHub.
        prs (list):
            List of related pull requests (designated by
            GitHub keywords). Pull requests are sorted by
            creation date (DESC).

    Returns:
        bool:
            True if issue should be deleted from the
            spreadsheet, False otherwise.
    """
    if issue and issue.closed_at and row["Assignee"] in ("Other", "N/A"):
        return True
    return False


def to_be_ignored(issue):
    """Condition function to designate if issue shouldn't be tracked.

    Unlike to_be_deleted() function, which implements table
    cleanup, this function is used to completely ignore issues.
    If the function returns True, issue will not be added into
    the table and tracked in future.

    Args:
        issue (github.Issue.Issue):
            Issue which pretends to be added into the table.

    Returns:
        bool:
            True if issue should be ignored. False if issue
            should be added into the table and tracked.
    """
    # On a first update after Scraper start last opened issue
    # update time will be recorded. On a next update it'll be
    # used as "since" filter. With this, issues, which were closed
    # after last opened issue update time will appear in table.
    # Ignore these issues.
    if not issue.closed_at:
        return False

    date_diff = datetime.date.today() - issue.closed_at.date()
    if date_diff.days > 3:
        return True
    return False


def to_be_archived(row):
    """Condition function to designate if issue should be archived.

    Args:
        row (dict): Row to be checked.

    Returns:
        bool: True if issue should archived, False otherwise.
    """
    return row["Priority"] == "Done"


def sort_func(row):
    """Sorts data within sheet.

    Args:
        row (dict): Dict representation of a single row.
    """
    return row["Repository"], row["Project"], int(get_num_from_formula(row["Issue"]))


def archive_sort_func(row):
    """Sorts data in the archive sheet.

    Args:
        row (dict): Dict representation of a single row.
    """
    return row["Sheet"], row["Project"], int(get_num_from_formula(row["Issue"]))


def _designate_status_color(pull, team):
    """Check PR status and return corresponding color.

    Args:
        pull (github.PullRequest.PullRequest):
            Pull request object.

    Returns:
        dict: Color to fill the cell.
    """
    if pull.user.login not in team:
        # yellow
        return {"red": 1, "green": 0.81, "blue": 0.28}

    if pull.merged:
        # purple
        return {"red": 0.73, "green": 0.33, "blue": 0.83}

    if pull.state == "closed":
        # pink
        return {"red": 1, "green": 0.36, "blue": 0.47}

    return {"red": 1, "green": 1, "blue": 1}
