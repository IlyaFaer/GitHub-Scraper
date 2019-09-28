"""
Functions, which are used for filling columns in
a single one row. Fill free to redefine.

Every filling function accepts two args:

old_issue (Row): Dict-like object, which represents
row, retrieved from a spreadsheet. Redact it's values to
update row values in spreadsheet.

issue (github.Issue.Issue): Issue object, read from GitHub.

sheet_name (str): Name of target sheet.

sheet_config (dict): Sheet configurations from config.py.
"""
import datetime
from utils import build_url_formula


def fill_priority(old_issue, issue, sheet_name, sheet_config):
    """'Priority' column filling."""
    # new issue
    if old_issue == issue:
        old_issue["Priority"] = "New"
        return

    issue = issue["Issue_obj"]
    date_diff = datetime.date.today() - issue.created_at.date()
    # if issue have been new for three or more days,
    # auto designate it's priority
    if old_issue["Priority"] == "New" and date_diff.days > 3:
        our_labels = []
        labels = [label.name for label in issue.labels]

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
            # bugs in our projects have high priority
            if "type: bug" in labels:
                old_issue["Priority"] = "High"
            # other issues
            else:
                old_issue["Priority"] = "Medium"
        # other projects
        else:
            old_issue["Priority"] = "Low"


def fill_issue(old_issue, issue, sheet_name, sheet_config):
    """'Issue' column filling."""
    issue = issue["Issue_obj"]
    old_issue["Issue"] = build_url_formula(issue)


def fill_status(old_issue, issue, sheet_name, sheet_config):
    """'Work status' column filling."""
    if old_issue == issue:
        old_issue["Work status"] = "Pending"


def fill_created(old_issue, issue, sheet_name, sheet_config):
    """'Created' column filling."""
    issue = issue["Issue_obj"]
    old_issue["Created"] = issue.created_at.strftime("%d %b %Y")


def fill_description(old_issue, issue, sheet_name, sheet_config):
    """'Description' column filling."""
    issue = issue["Issue_obj"]
    old_issue["Description"] = issue.title


def fill_assignee(old_issue, issue, sheet_name, sheet_config):
    """'Assignee' column filling."""
    issue = issue["Issue_obj"]

    assignee = issue.assignee
    if old_issue["Assignee"] not in sheet_config["team"]:
        if assignee:
            old_issue["Assignee"] = (
                assignee.login if assignee.login in sheet_config["team"] else "Other"
            )
        else:
            old_issue["Assignee"] = "N/A"


def dont_fill(old_issue, issue, sheet_name, sheet_config):
    """
    Dummy fill function, default for
    columns with no 'fill_func' field.
    """
    pass
