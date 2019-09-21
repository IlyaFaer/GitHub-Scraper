"""
Functions, which fills columns in issues/PRs
tables. Fill free to redefine.
"""
import datetime


def fill_priority(old_issue, issue):
    """Fill column 'Priority' of a single one issue.

    Args:
        old_issue (Row): Existing row of a table.

        issue (github.Issue.Issue): Issue object, read from GitHub.
    """
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


def dont_fill(old_issue, issue):
    """
    Dummy fill function, default for
    columns with no 'fill_func' field.
    """
    pass
