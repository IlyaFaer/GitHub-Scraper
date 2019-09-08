"""
File that describes spreadsheet's architecture, including
columns style, data validation, tracked repositories,
tracked fields, etc..
"""
from const import GREY, GREEN, BLUE, PINK, RED_KRAYOLA, GREEN_GOOD, WHITE, YELLOW
from utils import get_num_from_url


TITLE = "QLogic Internal Review"  # spreadsheet title
UPDATE_PERIODICITY = 3600  # duration of pause between updates

# sheets structure
SHEETS = {
    # -----------------------------
    "Python": {  # sheet name
        "labels": {  # meaningful labels
            "api: storage": "Storage",
            "api: firestore": "FireStore",
            "api: bigquery": "BigQuery",
            "api: bigtable": "BigTable",
            "api: spanner": "Spanner",
            "api: pubsub": "PubSub",
            "api: core": "Core",
            "api: datastore": "Datastore",
        },
        "repo_names": {  # repos to track
            "googleapis/google-cloud-python": "GCP",
            "googleapis/google-resumable-media-python": "GRMP",
            "q-logic/google-cloud-python": "Q-GCP",
            "q-logic/google-resumable-media-python": "Q-GRMP",
        },
        "team": {  # team, that works in this repos
            "Ilya": "IlyaFaer",
            "Hemang": "HemangChothani",
            "Maxim": "mf2199",
            "Paras": "pchauhan-qlogic",
            "Sumit": "sumit-ql",
            "Sangram": "sangramql",
            "Leonid": "Emar-Kar",
            "N/A": "",
            "Other": "Other",
        },
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
        "team": {
            "Lalji": "laljikanjareeya",
            "Praveen": "praveenqlogic01",
            "Jiren": "jiren",
            "Vishal": "vishald123",
            "Alex": "AVaksman",
            "Ivan": "IvanAvanessov",
            "N/A": "",
            "Other": "Other",
        },
    },
    # -----------------------------
    "Golang": {
        "labels": {
            "api: storage": "Storage",
            "api: firestore": "FireStore",
            "api: bigquery": "BigQuery",
            "api: bigtable": "BigTable",
            "api: spanner": "Spanner",
            "api: pubsub": "PubSub",
        },
        "repo_names": {"googleapis/google-cloud-go": "GCG"},
        "team": {
            "Ilya": "IlyaFaer",
            "Aleksandra": "AlesskaPie",
            "Emmanuel": "odeke-em",
            "N/A": "",
            "Other": "Other",
        },
    },
}

# fields, that must be updated on every sheet update
# other fields will be left unchanged
TRACKED_FIELDS = ("Created", "Description", "Project", "Assignee")

# columns structure
COLUMNS = (
    {
        "name": "Priority",  # 0
        "width": 80,
        "align": "CENTER",
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
