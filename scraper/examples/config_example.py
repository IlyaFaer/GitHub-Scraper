"""
File describes spreadsheet's architecture, including
columns style, data validation, tracked repositories, etc.

This is a configurations example. Create and tweak your
own config.py (see TODO). Your config.py will not be Git-tracked.
"""
import copy
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

# TODO: set your spreadsheet title
TITLE = "QLogic Issue Tracker"
# TODO: set duration of a pause between updates
UPDATE_PERIODICITY = 3600  # one hour

# TODO: set your table structure
COLUMNS = [
    {
        "name": "Priority",  # column title
        "width": 80,
        "align": "CENTER",  # text alignment
        # function which sets a value of a
        # single one cell in this column
        "fill_func": fill_funcs.fill_priority,
        # possible values with their colors
        # column will become drop-down list
        "values": {
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
        "name": "Public PR",
        "align": "CENTER",
        "type": "link",
        "fill_func": fill_funcs.fill_ppr,
    },
    {"name": "Task", "align": "CENTER"},
    {"name": "Comment", "width": 550},
]

# team for every sheet
TEAMS = {
    "Python": [
        "IlyaFaer",
        "HemangChothani",
        "mf2199",
        "sangramql",
        "Emar-Kar",
        "paul1319",
        "Other",
        "N/A",
    ],
    "NodeJS": [
        "laljikanjareeya",
        "praveenqlogic01",
        "jiren",
        "vishald123",
        "AVaksman",
        "IvanAvanessov",
        "dmitry-fa",
        "Other",
        "N/A",
    ],
    "Golang": ["IlyaFaer", "AlisskaPie", "Other", "N/A"],
    "PHP": ["andrewinc", "ava12", "Other", "N/A"],
    "Java": ["athakor", "pmakani", "rahulKQL", "dmitry-fa", "Other", "N/A"],
}


# set teams into column settings (every sheet has it's own team)
GO_COLUMNS = copy.copy(COLUMNS)
GO_COLUMNS[7]["values"] = TEAMS["Golang"]

PY_COLUMNS = copy.deepcopy(COLUMNS)
PY_COLUMNS[7]["values"] = TEAMS["Python"]

JS_COLUMNS = copy.deepcopy(COLUMNS)
JS_COLUMNS[7]["values"] = TEAMS["NodeJS"]

PHP_COLUMNS = copy.deepcopy(COLUMNS)
PHP_COLUMNS[7]["values"] = TEAMS["PHP"]

JAVA_COLUMNS = copy.deepcopy(COLUMNS)
JAVA_COLUMNS[7]["values"] = TEAMS["Java"]

# TODO: set your spreadsheet structure
SHEETS = {
    # -----------------------------
    "Python": {  # sheet name
        "labels": projects_labels,  # meaningful labels
        "repo_names": {  # repos to track on this sheet
            # every key will be used with prefix: github.com/
            "googleapis/python-logging": "Logging",
            "googleapis/python-dataproc": "Dataproc",
            "googleapis/python-datastore": "Datastore",
            "googleapis/python-bigquery-storage": "BQ Storage",
            "googleapis/python-bigquery-datatransfer": "BQ Datatransfer",
            "googleapis/python-pubsub": "Pub/Sub",
            "googleapis/python-recommender": "Recommender",
            "googleapis/python-resource-manager": "Resource Manager",
            "googleapis/python-texttospeech": "Text To Speech",
            "googleapis/python-translate": "Translate",
            "googleapis/python-vision": "Vision",
            "googleapis/python-speech": "Speech",
            "googleapis/python-bigquery": "BigQuery",
            "googleapis/python-runtimeconfig": "Runtime Config",
            "googleapis/python-scheduler": "Scheduler",
            "googleapis/python-securitycenter": "Security Center",
            "googleapis/python-tasks": "Tasks",
            "googleapis/python-billingbudgets": "Billing Budgets",
            "googleapis/python-videointelligence": "Video Intelligence",
            "googleapis/python-ndb": "NDB",
            "googleapis/python-trace": "Trace",
            "googleapis/python-talent": "Talent",
            "googleapis/python-iam": "IAM",
            "googleapis/python-redis": "Redis",
            "googleapis/python-firestore": "Firestore",
            "googleapis/python-container": "Container",
            "googleapis/python-dlp": "DLP",
            "googleapis/python-documentai": "Document AI",
            "googleapis/python-storage": "Storage",
            "googleapis/python-dns": "DNS",
            "googleapis/python-spanner": "Spanner",
            "googleapis/python-datalabeling": "Data Labeling",
            "googleapis/python-containeranalysis": "Container Analysis",
            "googleapis/python-datacatalog": "Data Catalog",
            "googleapis/python-cloudbuild": "Cloud Build",
            "googleapis/python-bigtable": "BigTable",
            "googleapis/python-automl": "Auto ML",
            "googleapis/python-webrisk": "Webrisk",
            "googleapis/python-websecurityscanner": "Security Scanner",
            "googleapis/python-api-core": "API Core",
            "googleapis/python-secret-manager": "Secret Manager",
            "googleapis/google-resumable-media-python": "GRMP",
        },
        # columns configurations for this sheet
        "columns": PY_COLUMNS,
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
        "columns": JS_COLUMNS,
    },
    # -----------------------------
    "Golang": {
        "labels": projects_labels,
        "repo_names": {
            "googleapis/google-cloud-go": "Cloud",
            "googleapis/google-api-go-client": "ApiClient",
        },
        "columns": GO_COLUMNS,
    },
    # -----------------------------
    "PHP": {
        "labels": projects_labels,
        "repo_names": {"googleapis/google-cloud-php": "GCPHP"},
        "columns": PHP_COLUMNS,
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
        "columns": JAVA_COLUMNS,
    },
}
