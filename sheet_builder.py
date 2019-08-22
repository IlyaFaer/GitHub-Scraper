"""
Utils for reading data from GitHub and building sheets
with this data.
"""
from github import Github
from config import SHEETS
from utils import gen_color_request, get_num_from_url
from const import YELLOW_RAPS, PINK, PURPLE
import re
import datetime


PATTERNS = (
    re.compile('Fixes[\:]? #[\d*]+'),
    re.compile('Closes[\:]? #[\d*]+'),
    re.compile('Towards[\:]? #[\d*]+'),
    re.compile('IPR[\:]? [\d*]+'),
)


with open('loginpas.txt') as login_file:
    login, password = login_file.read().split('/')

gh_client = Github(login, password)


class SheetBuilder:
    """Class that builds table of issues/PRs from specified repos."""
    def __init__(self, sheet_name, sheet_id):
        self._labels = SHEETS[sheet_name]['labels']
        self._repos = {}
        self._repo_names = SHEETS[sheet_name]['repo_names']
        self._repo_names_inverse = dict(
            (v, k) for k, v in self._repo_names.items()
        )
        self._prs_index = {}
        self._internal_prs_index = {}
        self._sheet_id = sheet_id
        self._sheet_name = sheet_name
        self._reverse_team = dict(
            (v, k) for k, v in SHEETS[sheet_name]['team'].items()
        )

    def build_table(self):
        """Build list of issues from given repositories.

        Returns: list of dicts.
        """
        self._prs_index = {}
        self._internal_prs_index = {}

        rows = []
        for repo_name in self._repo_names.keys():
            repo = self._get_repo(repo_name)
            oldest_issue_date = datetime.datetime(2000, 1, 1)

            # process open PRs and issues
            for issue in repo.get_issues():
                oldest_issue_date = min(
                    issue.created_at, oldest_issue_date
                )

                row = self._build_issue_dict(issue, repo)
                if row:
                    rows.append(row)

            self._index_closed_prs(repo, oldest_issue_date)

        return rows

    def build_url(self, num, repo_lts):
        """Build URL from issue number and repo name."""
        repo = self._repo_names_inverse[repo_lts]
        url = '=HYPERLINK("https://github.com/{repo}/issues/{num}";"{num}")'.format(
            repo=repo, num=num
        )
        return url

    def fill_prs(self, table):
        """Try autodetect PRs, using PRs indexes."""
        requests = []

        for index, issue in enumerate(table):
            num = get_num_from_url(issue[1])

            for prs_index, num_field, prefix in (
                (self._prs_index, 9, ''),
                (self._internal_prs_index, 8, 'Q-')
            ):

                if (num, prefix + issue[5]) in prs_index.keys():
                    pull, repo_name = prs_index.pop(
                        (num, prefix + issue[5])
                    )

                    if pull.number != num:
                        issue[num_field] = self.build_url(
                            pull.number, repo_name
                        )

                        color = self._designate_status_color(pull)
                        if color:
                            requests.append(gen_color_request(
                                self._sheet_id,
                                index + 1,
                                num_field,
                                color
                            ))
        return requests

    def _get_repo(self, repo_name):
        """Return repo object by name.

        If repo object already created, it'll be returned
        from inner index. Otherwise, it'll be created.

        Args:
            repo_name (str): Repo's name.

        Returns: github.Repository.Repository object.
        """
        repo = self._repos.get(repo_name)
        if repo is None:
            repo = gh_client.get_repo(repo_name)
            self._repos[repo_name] = repo

        return repo

    def _add_into_index(self, repo, repo_lts, lpr, result):
        # internal PR
        if repo.full_name.startswith('q-logic/'):
            self._internal_prs_index[
                result.split()[1], repo_lts
            ] = lpr
        # public PR
        else:
            self._prs_index[
                result.split('#')[1], repo_lts
            ] = lpr

    def _index_closed_prs(self, repo, since_date):
        """Add to index closed pull requests."""
        pulls = repo.get_pulls(
            state='closed', sort='created', direction='desc'
        )

        repo_lts = self._repo_names[repo.full_name]
        for pull in pulls:
            result = self._try_match_keywords(pull.body)
            if result:
                self._add_into_index(
                    repo, repo_lts, (pull, repo_lts), result
                )

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
            row['Priority'] = 'Medium'
            row['Issue'] = '=HYPERLINK("{url}";"{num}")'.format(
                num=issue.number, url=issue.html_url
            )
            row['Work status'] = 'Pending'
            row['Created'] = issue.created_at.strftime('%d %b %Y')
            row['Description'] = issue.title
            row['Repository'] = repo_lts
            row['Project'] = self._get_project_name(issue.get_labels())
            row['Assignee'] = 'N/A'
            assignee = issue.assignee
            if assignee:
                row['Assignee'] = self._reverse_team.get(assignee.login, 'Other')
        else:
            # add PR into index
            if not (issue.number, repo_lts) in self._prs_index.keys():
                result = self._try_match_keywords(issue.body)
                if result:
                    self._add_into_index(
                        repo,
                        repo_lts,
                        (issue.as_pull_request(), repo_lts),
                        result
                    )
        return row

    def _get_project_name(self, labels):
        """Designate project name by issue labels."""
        issue_labels = set()

        for label in labels:
            if 'api:' in label.name:
                label = self._labels.get(label.name, 'Other')
                issue_labels.add(label)

        issue_labels = sorted(list(issue_labels))
        return ', '.join(issue_labels)

    def _try_match_keywords(self, body):
        """
        Try to find keywords in issue's body.

        Args:
            body (str): Issue's body.

        Returns: Keyword with issue number, if found.
        """
        if body:
            for pattern in PATTERNS:
                result = pattern.findall(body)
                if result:
                    return result[0]

    def _designate_status_color(self, pull):
        """Check PR's status and return corresponding color."""
        status = None

        if pull.merged:
            status = PURPLE
        elif pull.state == 'closed' and not pull.merged:
            status = PINK
        elif pull.user.login not in SHEETS[self._sheet_name]['team'].values():
            status = YELLOW_RAPS

        return status
