"""
File describes spreadsheet's architecture, including
columns style, data validation, tracked repositories, etc.
"""
import copy
from utils import get_num_from_url
import fill_funcs
import const


# {<label name>: <project name>}
projects_labels = {
    "api: storage": "Storage",
    "api: firestore": "FireStore",
    "api: bigquery": "BigQuery",
    "api: bigquerystorage": "BigQuery Storage",
    "api: bigtable": "BigTable",
    "api: spanner": "Spanner",
    "api: pubsub": "PubSub",
    "api: core": "Core",
    "api: datastore": "Datastore",
}

TITLE = "QLogic Issue Tracker"  # spreadsheet title
UPDATE_PERIODICITY = 3600  # duration of pause between updates

# columns structure
COLUMNS = [
    {
        "name": "Priority",
        "width": 80,
        "align": "CENTER",
        "fill_func": fill_funcs.fill_priority,
        "values": {  # possible values with their colors
            "Closed": const.GREY,
            "Low": const.GREEN,
            "Medium": const.BLUE,
            "High": const.PINK,
            "Critical": const.RED_KRAYOLA,
            "Done": const.GREEN_GOOD,
            "New": const.WHITE,
        },
    },
    {
        "name": "Issue",
        "width": 50,
        "align": "CENTER",
        "type": "link",
        "fill_func": fill_funcs.fill_issue,
    },
    {
        "name": "Work status",
        "align": "CENTER",
        "fill_func": fill_funcs.fill_status,
        "values": {
            "Pending": const.WHITE,
            "In progress": const.GREEN,
            "Paused": const.YELLOW,
            "Finished": const.GREY,
        },
    },
    {
        "name": "Created",
        "align": "CENTER",
        "type": "date",
        "fill_func": fill_funcs.fill_created,
    },
    {"name": "Description", "width": 450, "fill_func": fill_funcs.fill_description},
    {"name": "Repository", "align": "CENTER", "fill_func": fill_funcs.fill_repository},
    {"name": "Project", "align": "CENTER", "fill_func": fill_funcs.fill_project},
    {"name": "Assignee", "align": "CENTER", "fill_func": fill_funcs.fill_assignee},
    {
        "name": "Internal PR",
        "align": "CENTER",
        "type": "link",
        "fill_func": fill_funcs.fill_ipr,
    },
    {
        "name": "Public PR",
        "align": "CENTER",
        "type": "link",
        "fill_func": fill_funcs.fill_ppr,
    },
    {"name": "Task", "align": "CENTER"},
    {"name": "Comment", "width": 550},
]

# we don't review code internally in Go
GO_COLUMNS = copy.copy(COLUMNS)
GO_COLUMNS.pop(8)

# sheets structure
SHEETS = {
    # -----------------------------
    "Python": {  # sheet name
        "labels": projects_labels,  # meaningful labels
        # repos to track
        "repo_names": {
            "googleapis/google-cloud-python": "GCP",
            "googleapis/google-resumable-media-python": "GRMP",
        },
        "internal_repo_names": {
            "q-logic/google-cloud-python": "GCP",
            "q-logic/google-resumable-media-python": "GRMP",
        },
        "team": [  # team, that works in this repos
            "IlyaFaer",
            "HemangChothani",
            "mf2199",
            "sumit-ql",
            "sangramql",
            "Emar-Kar",
            "paul1319",
            "Other",
            "N/A",
        ],
        # columns configurations for this sheet
        "columns": COLUMNS,
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
            "fazunenko",
            "Other",
            "N/A",
        ],
        "columns": COLUMNS,
    },
    # -----------------------------
    "Golang": {
        "labels": projects_labels,
        "repo_names": {
            "googleapis/google-cloud-go": "Cloud",
            "googleapis/google-api-go-client": "ApiClient",
        },
        "team": ["IlyaFaer", "AlisskaPie", "Other", "N/A"],
        "columns": GO_COLUMNS,
    },
    # -----------------------------
    "PHP": {
        "labels": projects_labels,
        "repo_names": {"googleapis/google-cloud-php": "GCPHP"},
        "internal_repo_names": {"q-logic/google-cloud-php": "GCPHP"},
        "team": ["andrewinc", "ava12", "Other", "N/A"],
        "columns": COLUMNS,
    },
    "Java": {
        "labels": projects_labels,
        "repo_names": {
            "googleapis/java-bigtable-hbase": "BT HBase",
            "googleapis/java-datalabeling": "Data Labeling",
            "googleapis/java-cloudbuild": "Cloud Build",
            "googleapis/java-automl": "Auto ML",
            "googleapis/java-speech": "Speech",
            "googleapis/java-dlp": "Data Loss Prevention",
            "googleapis/java-datacatalog": "Data Catalog",
            "googleapis/java-gameservices": "Game Services",
            "googleapis/java-iot": "IoT Core",
            "googleapis/java-errorreporting": "Stackdriver Error Reporting",
            "googleapis/java-dialogflow": "Dialogflow",
            "googleapis/java-dataproc": "Dataproc",
            "googleapis/java-grafeas": "Grafeas",
            "googleapis/java-dns": "DNS",
            "googleapis/java-language": "Language",
            "googleapis/java-iamcredentials": "IAM",
            "googleapis/java-irm": "Stackdriver Incident Response & Management",
            "googleapis/java-containeranalysis": "Container Analysis",
            "googleapis/java-os-login": "OS Login",
            "googleapis/java-tasks": "Tasks",
            "googleapis/java-texttospeech": "Text-to-Speech",
            "googleapis/java-resourcemanager": "Resource Manager",
            "googleapis/java-securitycenter": "Security Center",
            "googleapis/java-recaptchaenterprise": "reCAPTCHA Enterprise",
            "googleapis/java-bigquerydatatransfer": "BQ Datatransfer",
            "googleapis/java-bigtable": "Bigtable",
            "googleapis/java-datastore": "Datastore",
            "googleapis/google-api-java-client": "API Client",
            "googleapis/java-monitoring-dashboards": "Monitoring Dashboards",
            "googleapis/java-redis": "Redis",
            "googleapis/java-talent": "Talent",
            "googleapis/java-billingbudgets": "Billing Budgets",
            "googleapis/java-websecurityscanner": "Security Scanner",
            "googleapis/java-asset": "Asset",
            "googleapis/java-phishingprotection": "Phishing Protection",
            "googleapis/java-recommender": "Recommender",
            "googleapis/java-scheduler": "Scheduler",
            "googleapis/java-translate": "Translate",
            "googleapis/java-webrisk": "Webrisk",
            "googleapis/java-conformance-tests": "Conformance Tests",
            "googleapis/java-firestore": "Firestore",
            "googleapis/java-bigquery": "Bigquery",
            "googleapis/java-logging": "Logging",
            "googleapis/java-bigquerystorage": "Bigquery Storage",
            "googleapis/gax-java": "Gax",
            "googleapis/java-vision": "Vision",
            "googleapis/java-compute": "Compute",
            "googleapis/java-spanner": "Spanner",
            "googleapis/java-spanner-jdbc": "Spanner JDBC Driver",
            "googleapis/java-secretmanager": "Secret Manager",
            "googleapis/java-notification": "Notification",
            "googleapis/java-logging-logback": "Logback",
            "googleapis/java-core": "Core",
            "googleapis/java-storage": "Storage",
            "googleapis/java-trace": "Trace",
            "googleapis/java-video-intelligence": "Video Intelligence",
            "googleapis/java-kms": "KMS",
            "googleapis/java-monitoring": "Monitoring",
            "googleapis/java-container": "Container",
            "googleapis/google-http-java-client": "HTTP Client",
            "googleapis/google-auth-library-java": "Auth Library",
            "googleapis/java-storage-nio": "Storage NIO",
            "googleapis/api-common-java": "Common API",
            "googleapis/java-document-ai": "Document AI",
            "googleapis/api-compiler": "API Compiler",
            "googleapis/common-protos-java": "Common Protos",
        },
        "internal_repo_names": {},
        "team": ["athakor", "pmakani", "rahulKQL", "fazunenko", "Other", "N/A"],
        "columns": COLUMNS,
    },
}


def sort_func(row):
    """Function sorts data within sheet.

    Args:
        row (dict): Dict representation of single row.
    """
    return row["Repository"], row["Project"], int(get_num_from_url(row["Issue"]))
