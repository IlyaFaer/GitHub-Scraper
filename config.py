"""
File that describes spreadsheet's architecture, including
columns style, data validation, tracked repositories,
tracked fields, etc..
"""
from const import GREY, GREEN, BLUE, PINK, RED_KRAYOLA, GREEN_GOOD, WHITE, YELLOW
from utils import get_num_from_url
from fill_funcs import fill_priority


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
        "labels": projects_labels,
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
        "team": ["IlyaFaer", "AlisskaPie", "andrewelkin", "Other", "N/A"],
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

# fields, that must be updated on every sheet update
# other fields will be left unchanged
TRACKED_FIELDS = ("Priority", "Created", "Description", "Project", "Assignee")

# columns structure
COLUMNS = (
    {
        "name": "Priority",  # 0
        "width": 80,
        "align": "CENTER",
        "fill_func": fill_priority,
        "values": {  # possible value with it's color
            "Closed": GREY,
            "Low": GREEN,
            "Medium": BLUE,
            "High": PINK,
            "Critical": RED_KRAYOLA,
            "Done": GREEN_GOOD,
            "New": WHITE,
        },
    },
    {"name": "Issue", "width": 50, "align": "CENTER", "type": "link"},  # 1
    {
        "name": "Work status",  # 2
        "align": "CENTER",
        "values": {
            "Pending": WHITE,
            "In progress": GREEN,
            "Paused": YELLOW,
            "Finished": GREY,
        },
    },
    {"name": "Created", "align": "CENTER", "type": "date"},  # 3
    {"name": "Description", "width": 450},  # 4
    {"name": "Repository", "align": "CENTER"},  # 5
    {"name": "Project", "align": "CENTER"},  # 6
    {"name": "Assignee", "align": "CENTER"},  # 7
    {"name": "Internal PR", "align": "CENTER", "type": "link"},  # 8
    {"name": "Public PR", "align": "CENTER", "type": "link"},  # 9
    {"name": "Task", "align": "CENTER"},  # 10
    {"name": "Opened", "align": "CENTER", "type": "date"},  # 11
    {"name": "Comment", "width": 550},  # 12
)


def sort_func(row):
    """Function that sorts data in the sheet.

    Args:
        row (dict): Dict representation of single row.
    """
    return row["Repository"], row["Project"], int(get_num_from_url(row["Issue"]))
