"""
File describes spreadsheet's architecture, including
columns style, data validation, tracked repositories,
tracked fields, etc..
"""
from const import GREY, GREEN, BLUE, PINK, RED_KRAYOLA, GREEN_GOOD, WHITE, YELLOW
from utils import get_num_from_url
import fill_funcs


projects_labels = {
    "api: storage": "Storage",
    "api: firestore": "FireStore",
    "api: bigquery": "BigQuery",
    "api: bigtable": "BigTable",
    "api: spanner": "Spanner",
    "api: pubsub": "PubSub",
    "api: core": "Core",
    "api: datastore": "Datastore",
}

TITLE = "QLogic Internal Review"  # spreadsheet title
UPDATE_PERIODICITY = 3600  # duration of pause between updates

# sheets structure
SHEETS = {
    # -----------------------------
    "Python": {  # sheet name
        "labels": projects_labels,  # meaningful labels
        "repo_names": {  # repos to track
            "googleapis/google-cloud-python": "GCP",
            "googleapis/google-resumable-media-python": "GRMP",
            "q-logic/google-cloud-python": "Q-GCP",
            "q-logic/google-resumable-media-python": "Q-GRMP",
        },
        "team": [  # team, that works in this repos
            "IlyaFaer",
            "HemangChothani",
            "mf2199",
            "sumit-ql",
            "sangramql",
            "Emar-Kar",
            "Other",
            "N/A",
        ],
    },
    # -----------------------------
    "NodeJS": {
        "labels": {},
        "repo_names": {
            "googleapis/nodejs-storage": "Storage",
            "googleapis/nodejs-firestore": "FireStore",
            "googleapis/nodejs-bigquery": "BigQuery",
            "googleapis/nodejs-spanner": "Spanner",
            "googleapis/nodejs-bigtable": "BigTable",
            "googleapis/nodejs-pubsub": "PubSub",
        },
        "team": [
            "laljikanjareeya",
            "praveenqlogic01",
            "jiren",
            "vishald123",
            "AVaksman",
            "IvanAvanessov",
            "Other",
            "N/A",
        ],
    },
    # -----------------------------
    "Golang": {
        "labels": projects_labels,
        "repo_names": {"googleapis/google-cloud-go": "GCG"},
        "team": ["IlyaFaer", "AlisskaPie", "Other", "N/A"],
    },
    # -----------------------------
    "PHP": {
        "labels": projects_labels,
        "repo_names": {
            "googleapis/google-cloud-php": "GCPHP",
            "q-logic/google-cloud-php": "Q-GCPHP",
        },
        "team": ["andrewinc", "Other", "N/A"],
    },
}

# columns structure
COLUMNS = (
    {
        "name": "Priority",  # 0
        "width": 80,
        "align": "CENTER",
        "fill_func": fill_funcs.fill_priority,
        "values": {  # possible values with their color
            "Closed": GREY,
            "Low": GREEN,
            "Medium": BLUE,
            "High": PINK,
            "Critical": RED_KRAYOLA,
            "Done": GREEN_GOOD,
            "New": WHITE,
        },
    },
    {
        "name": "Issue",  # 1
        "width": 50,
        "align": "CENTER",
        "type": "link",
        "fill_func": fill_funcs.fill_issue,
    },
    {
        "name": "Work status",  # 2
        "align": "CENTER",
        "fill_func": fill_funcs.fill_status,
        "values": {
            "Pending": WHITE,
            "In progress": GREEN,
            "Paused": YELLOW,
            "Finished": GREY,
        },
    },
    {
        "name": "Created",  # 3
        "align": "CENTER",
        "type": "date",
        "fill_func": fill_funcs.fill_created,
    },
    {
        "name": "Description",  # 4
        "width": 450,
        "fill_func": fill_funcs.fill_description,
    },
    {
        "name": "Repository",
        "align": "CENTER",
        "fill_func": fill_funcs.fill_repository,
    },  # 5
    {"name": "Project", "align": "CENTER", "fill_func": fill_funcs.fill_project},  # 6
    {"name": "Assignee", "align": "CENTER", "fill_func": fill_funcs.fill_assignee},  # 7
    {"name": "Internal PR", "align": "CENTER", "type": "link"},  # 8
    {"name": "Public PR", "align": "CENTER", "type": "link"},  # 9
    {"name": "Task", "align": "CENTER"},  # 10
    {"name": "Opened", "align": "CENTER", "type": "date"},  # 11
    {"name": "Comment", "width": 550},  # 12
)


def sort_func(row):
    """Function sorts data in the sheet.

    Args:
        row (dict): Dict representation of single row.
    """
    return row["Repository"], row["Project"], int(get_num_from_url(row["Issue"]))
