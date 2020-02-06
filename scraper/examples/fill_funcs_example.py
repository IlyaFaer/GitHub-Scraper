"""
Functions, which are used for filling columns in
a single one row. Fill free to redefine.

This is a filling functions example. Create and tweak
your own fill_funcs.py. Your fill_funcs.py will not
be Git-tracked.

Every filling function accepts:

old_issue (Row): Dict-like object, which represents
row, retrieved from a spreadsheet. Redact it's values to
update row values in spreadsheet. Use it's colors attribute
for coloring cells.

issue (github.Issue.Issue): Issue object, read from GitHub.

sheet_name (str): Name of target sheet.

sheet_config (dict): Sheet configurations from config.py.

prs (dict): Lists of related internal and public
pull requests (designated by GitHub keywords).
Pull requests are sorted by creation date (DESC).

is_new (bool): New issue in table.
"""
import datetime
from const import GREY
from utils import build_url_formula, designate_status_color, get_num_from_formula


def fill_priority(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Priority' column filling."""
    if is_new:
        old_issue["Priority"] = "New"
        return

    date_diff = datetime.date.today() - issue.created_at.date()
    # if issue have been new for three or more days,
    # auto designate it's priority
    labels = [label.name for label in issue.labels]

    if old_issue["Priority"] not in ("Closed", "Done"):
        if "backend" in labels:
            old_issue["Priority"] = "Low"
        elif "help wanted" in labels:
            old_issue["Priority"] = "High"
        elif old_issue["Priority"] == "New":
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
                    # bugs and help requests are prioritized
                    if "type: bug" in labels:
                        old_issue["Priority"] = "High"
                    # other issues
                    else:
                        old_issue["Priority"] = "Medium"
                # other projects
                else:
                    old_issue["Priority"] = "Low"


def fill_issue(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Issue' column filling."""
    if is_new:
        old_issue["Issue"] = build_url_formula(issue)

    if issue.closed_at:
        old_issue.colors["Issue"] = GREY


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
    one_of_us = False

    if issue.assignees:
        for assignee in issue.assignees:
            if assignee.login in sheet_config["columns"][7]["values"]:
                one_of_us = True
                old_issue["Assignee"] = assignee.login
                break
        if not one_of_us:
            old_issue["Assignee"] = "Other"
    else:
        old_issue["Assignee"] = "N/A"


def fill_repository(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Repository' column filling."""
    # new issue
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
    if prs["public"]:
        last_pr = prs["public"][0]

        old_issue["Public PR"] = build_url_formula(last_pr)
        old_issue.colors["Public PR"] = designate_status_color(
            last_pr, sheet_config["columns"][7]["values"]
        )


def fill_ipr(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """'Internal PR' column filling."""
    if prs["internal"]:
        last_pr = prs["internal"][0]

        old_issue["Internal PR"] = build_url_formula(last_pr)
        old_issue.colors["Internal PR"] = designate_status_color(
            last_pr, sheet_config["columns"][7]["values"]
        )


def dont_fill(old_issue, issue, sheet_name, sheet_config, prs, is_new):
    """
    Dummy fill function, default for
    columns with no 'fill_func' field.
    """
    pass


def to_be_deleted(row, issue, prs):
    """
    Cleanup function, which designates if issue should be
    deleted from the spreadsheet.

    Args:
        row (Row): Dict-like object, which represents
            row, retrieved from a spreadsheet.
        issue (github.Issue.Issue): Issue object, read from GitHub.
        prs (dict): Lists of related internal and public
            pull requests (designated by GitHub keywords).
            Pull requests are sorted by creation date (DESC).

    Returns:
        bool:
            True if issue should be deleted from the
            spreadsheet, False otherwise.
    """
    if issue and issue.closed_at and row["Assignee"] in ("Other", "N/A"):
        return True
    return False


def sort_func(row):
    """Sorts data within single one sheet.

    Args:
        row (dict): Dict representation of a single row.
    """
    return row["Repository"], row["Project"], int(get_num_from_formula(row["Issue"]))
