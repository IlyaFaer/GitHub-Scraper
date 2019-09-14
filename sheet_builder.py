"""
Utils for reading data from GitHub and building
them into structures.
"""
from github import Github
from utils import gen_color_request, get_num_from_url
from const import YELLOW_RAPS, PINK, PURPLE, PATTERNS
import datetime


# authenticate in GitHub
with open("loginpas.txt") as login_file:
    login, password = login_file.read().split("/")

gh_client = Github(login, password)


class SheetBuilder:
    """Class that builds table of issues/PRs from specified repos."""

    def __init__(self, sheet_name, sheet_id):
        self._labels = {}
        self._repos = {}
        self._repo_names = {}
        self._repo_names_inverse = {}
        self._prs_index = {}
        self._internal_prs_index = {}
        # since this date we're looking for PRs
        self._oldest_issue_dates = {}
        self._team = []

        self._sheet_name = sheet_name
        self._sheet_id = sheet_id

    def build_table(self):
        """Build list of issues/PRs from given repositories.

        Returns: list of dicts, each of which represents
            single row.
        """
        rows = []
        for repo_name in self._repo_names.keys():
            repo = self._get_repo(repo_name)
            self._oldest_issue_dates[repo_name] = datetime.datetime(2000, 1, 1)

            # process open PRs and issues
            for issue in repo.get_issues():
                self._oldest_issue_dates[repo_name] = min(
                    issue.created_at, self._oldest_issue_dates[repo_name]
                )

                row = self._build_issue_dict(issue, repo)
                if row:
                    rows.append(row)

        return rows

    def build_url_formula(self, issue):
        """Build formula with issue's URL.

        Args:
            issue (github.Issue.Issue): Issue/PR object.

        Returns: issue's link (str).
        """
        url = '=HYPERLINK("{url}";"{num}")'.format(num=issue.number, url=issue.html_url)
        return url

    def fill_prs(self, table, closed_issues):
        """Try autodetect connections between PRs and issues.

        Uses previously built PR indexes.

        Args:
            table (list): Lists, each of which represents single row.

            closed_issues (list): Closed issues still must be updated
                to make easier match between new and old tables.

        Returns: list of requests with coloring data.
        """
        requests = []

        for repo_name in self._repo_names.keys():
            self._index_closed_prs(
                self._get_repo(repo_name), self._oldest_issue_dates[repo_name]
            )

        for index, issue in enumerate(table):
            num = get_num_from_url(issue[1])

            for prs_index, num_field, prefix in (
                (self._prs_index, 9, ""),
                (self._internal_prs_index, 8, "Q-"),
            ):

                if (num, prefix + issue[5]) in prs_index.keys():
                    pull, repo_name = prs_index.pop((num, prefix + issue[5]))

                    if pull.number != num:
                        pr_url = self.build_url_formula(pull)
                        try:
                            closed_ind = closed_issues.index(issue)
                            closed_issues[closed_ind][num_field] = pr_url
                        except ValueError:
                            pass

                        issue[num_field] = pr_url

                        color = self._designate_status_color(pull)
                        if color:
                            requests.append(
                                gen_color_request(
                                    self._sheet_id, index + 1, num_field, color
                                )
                            )
        return requests

    def update_config(self, config):
        """Update builder's configurations.

        Args:
            config (dict): Dict with sheet's configurations.
        """
        self._prs_index = {}
        self._internal_prs_index = {}
        self._oldest_issue_dates = {}

        self._labels = config["labels"]
        self._repo_names = config["repo_names"]
        self._repo_names_inverse = dict((v, k) for k, v in self._repo_names.items())
        self._team = config["team"]

    def _get_repo(self, repo_name):
        """Return repo object by name.

        If repo object already created, it'll be returned
        from inner index. Otherwise, it'll be created.

        Args:
            repo_name (str): Repo name.

        Returns: github.Repository.Repository object.
        """
        repo = self._repos.get(repo_name)
        if repo is None:
            repo = gh_client.get_repo(repo_name)
            self._repos[repo_name] = repo

        return repo

    def _add_into_index(self, repo, repo_lts, lpr, key_exp):
        """Add PR into inner index for future use.

        In table only last PR will be shown.

        Args:
            repo (github.Repository.Repository):
                Repository object.

            repo_lts (str): Short repo name.

            lpr (github.PullRequest.PullRequest):
                Pull request object.

            key_exp (str): Key expression, that contains
                linked issue number.
        """
        # internal PR
        if repo.full_name.startswith("q-logic/"):
            issue_num = key_exp.split()[1]
            if not (issue_num, repo_lts) in self._internal_prs_index:
                self._internal_prs_index[issue_num, repo_lts] = lpr
        # public PR
        else:
            issue_num = key_exp.split("#")[1]
            if not (issue_num, repo_lts) in self._prs_index:
                self._prs_index[issue_num, repo_lts] = lpr

    def _index_closed_prs(self, repo, since_date):
        """Add to PRs index closed pull requests.

        Args:
            repo (github.Repository.Repository):
                Repository object.

            since_data (datetime.datetime):
                Date of the oldest tracked issue. PRs
                which was created before this date, are
                meaningless.
        """
        pulls = repo.get_pulls(state="closed", sort="created", direction="desc")

        repo_lts = self._repo_names[repo.full_name]
        for pull in pulls:
            key_phrases = self._try_match_keywords(pull.body)
            for key_phrase in key_phrases:
                self._add_into_index(repo, repo_lts, (pull, repo_lts), key_phrase)

    def _build_issue_dict(self, issue, repo):
        """
        Build dict filled with issue data.
        If issue is PR, add it into index.

        Args:
            issue (github.Issue.Issue): Issue object.

            repo (github.Repository.Repository): Repository object.

        Returns: dict representation of single row.
        """
        row = {}
        repo_lts = self._repo_names[repo.full_name]
        if issue.pull_request is None:
            row["Priority"] = "Medium"
            row["Issue"] = self.build_url_formula(issue)
            row["Work status"] = "Pending"
            row["Created"] = issue.created_at.strftime("%d %b %Y")
            row["Description"] = issue.title
            row["Repository"] = repo_lts
            row["Project"] = self._get_project_name(issue.get_labels())
            row["Assignee"] = "N/A"
            assignee = issue.assignee
            if assignee:
                row["Assignee"] = (
                    assignee.login if assignee.login in self._team else "Other"
                )
        else:
            # add PR into index
            if not (issue.number, repo_lts) in self._prs_index.keys():
                key_phrases = self._try_match_keywords(issue.body)
                for key_phrase in key_phrases:
                    self._add_into_index(
                        repo, repo_lts, (issue.as_pull_request(), repo_lts), key_phrase
                    )
        return row

    def _get_project_name(self, labels):
        """Designate project name by issue labels."""
        issue_labels = set()

        for label in labels:
            if "api:" in label.name:
                label = self._labels.get(label.name, "Other")
                issue_labels.add(label)

        issue_labels = sorted(list(issue_labels))
        return ", ".join(issue_labels)

    def _try_match_keywords(self, body):
        """Try to find keywords in issue's body.

        Args:
            body (str): Issue's body.

        Returns: List of key phrases with issue numbers, if found.
        """
        if body:
            for pattern in PATTERNS:
                result = pattern.findall(body)
                if result:
                    return result
        return []

    def _designate_status_color(self, pull):
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
        elif pull.user.login not in self._team:
            status = YELLOW_RAPS

        return status
