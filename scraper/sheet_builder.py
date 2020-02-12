"""
Utils for reading data from GitHub and building
them into convenient structures.
"""
import datetime
import logging
from const import PATTERNS
from github import Github
from pr_index import PullRequestsIndex


class SheetBuilder:
    """Class that builds table of issues/PRs from specified repos.

    SheetBuilder should be used only for the single one
    specific sheet, meaning all of the repositories set
    to be tracked by this builder, will be shown on this sheet.
    """

    def __init__(self):
        self._repos = {}  # repos tracked by this builder
        self._repo_names = {}
        self._in_repo_names = {}
        self._repo_names_inverse = {}
        # time when any PR was last updated in every repo
        self._last_pr_updates = {}
        # time when any issue was last updated in every repo
        self._last_issue_updates = {}
        self.prs_index = PullRequestsIndex()
        # dict in which we aggregate all of the issue objects
        # used to avoid re-reading unupdated issues from GitHub
        self._issues_index = {}
        self._gh_client = None  # GitHub client object
        self.first_update = True
        self._login_on_github()

    def retrieve_updated(self):
        """Build list of issues/PRs from the given repositories.

        If this is the first update, than retrieve all of the
        opened issues. If update is subsequent, than only issues
        (opened and closed), which were updated since the last
        update will be processed.

        Returns:
            dict:
                Index of issues in format:
                {(issue.number, repo_short_name): github.Issue.Issue}
        """
        issue_index = {}
        repo_names = list(self._repo_names.keys()) + list(self._in_repo_names.keys())

        for repo_name in repo_names:
            repo = self._repos.setdefault(
                repo_name, self._gh_client.get_repo(repo_name)
            )
            self._index_closed_prs(repo)

            # process issues from the repo
            for issue in repo.get_issues(**self._build_filter(repo_name)):
                id_ = self._build_issues_id(issue, repo)
                if id_:
                    issue_index[id_] = issue

                last_issue_update = self._last_issue_updates.setdefault(
                    repo_name, datetime.datetime(1, 1, 1)
                )
                self._last_issue_updates[repo_name] = max(
                    last_issue_update, issue.updated_at
                )

        self._issues_index.update(issue_index)
        return issue_index

    def get_from_index(self, tracked_id):
        """Get issue object saved in internal index.

        Args:
            tracked_id (list): Issue number and repo short name.

        Returns:
            github.Issue.Issue: Issue object from index.
        """
        return self._issues_index.get(tracked_id)

    def delete_from_index(self, tracked_id):
        """Delete issue from internal index.

        Args:
            tracked_id (list): Issue number and repo short name.
        """
        self._issues_index.pop(tracked_id)

    def read_issue(self, issue_num, repo_lts):
        """Read issue by it's number and repository short name.

        Args:
            issue_num (str): Number of issue.
            repo_lst (str): Repository short name.

        Returns:
            github.Issue.Issue: Issue object from GitHub.
        """
        repo_name = self._repo_names_inverse.get(repo_lts)
        if repo_name is None:
            return

        repo = self._repos.get(repo_name)
        issue = repo.get_issue(int(issue_num))
        self._issues_index[(issue_num, repo_lts)] = issue
        return issue

    def reload_config(self, config):
        """Update builder's configurations - list of tracked repos.

        Args:
            config (dict): Dict with sheet's configurations.
        """
        self._repo_names = config["repo_names"]
        self._in_repo_names = config.get("internal_repo_names", {})

        self.prs_index.reload_config(self._in_repo_names)
        self._repo_names_inverse = dict((v, k) for k, v in self._repo_names.items())

    def get_related_prs(self, issue_id):
        """Return internal and public pull requests of specified issue.

        Args:
            issue_id (tuple): Issue number and repo short name.

        Returns:
            dict:
                All of the internal and public pull requests
                related to the specified issue.
        """
        return self.prs_index.get_related_prs(issue_id)

    def _build_filter(self, repo_name):
        """Build filter for get_issue() method.

        Args:
            repo_name (str):
                Name of the repo, which issues we're going to requests.

        Returns:
            dict: Filter, ready to be passed into the method.
        """
        args = {}
        if repo_name in self._last_issue_updates:
            # if it isn't the first get-issues request, than
            # we're adding sorting and "since" filter
            # to get only recently updated issues
            args = {
                "sort": "updated",
                "direction": "desc",
                "since": self._last_issue_updates[repo_name],
                "state": "all",
            }
        return args

    def _get_repo_lts(self, repo):
        """Get repo short name.

        Args:
            repo (github.Repository.Repository):
                Repository object.

        Returns:
            str: Repository short name.
        """
        repo_lts = self._repo_names.get(repo.full_name)
        if repo_lts is None:
            repo_lts = self._in_repo_names.get(repo.full_name)

        return repo_lts

    def _login_on_github(self):
        """Authenticate on GitHub."""
        with open("loginpas.txt") as login_file:
            login, password = login_file.read().strip().split("/")

        self._gh_client = Github(login, password)

    def _index_closed_prs(self, repo):
        """Add closed pull requests into PRs index.

        Method remembers last PR's update time and doesn't
        indexate PRs which weren't updated since last
        spreadsheet update.

        Args:
            repo (github.Repository.Repository):
                Repository object.
        """
        is_first_update = False
        pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")

        if pulls.totalCount:
            logging.info("{repo}: indexing pull requests".format(repo=repo.full_name))
            for index, pull in enumerate(pulls):
                if repo.full_name not in self._last_pr_updates.keys():
                    self._last_pr_updates[repo.full_name] = datetime.datetime(1, 1, 1)
                    is_first_update = True

                if pull.updated_at < self._last_pr_updates[repo.full_name]:
                    break

                key_phrases = self._try_match_keywords(pull.body)
                for key_phrase in key_phrases:
                    self.prs_index.add(repo, self._get_repo_lts(repo), pull, key_phrase)

                if is_first_update and pulls.totalCount > 800:
                    if (index + 1) % 200 == 0:
                        logging.info(
                            "processed {num} of {total} pull requests".format(
                                num=index + 1, total=pulls.totalCount
                            )
                        )

            self._last_pr_updates[repo.full_name] = pulls[0].updated_at
            logging.info(
                "{repo}: all pull requests indexed".format(repo=repo.full_name)
            )

    def _build_issues_id(self, issue, repo):
        """Designate issue's id. If issue is PR, index it.

        Args:
            issue (github.Issue.Issue): Issue object.

            repo (github.Repository.Repository): Repository object.

        Returns:
            tuple: issue's number and repo short name.
        """
        id_ = ()
        repo_lts = self._get_repo_lts(repo)

        if issue.pull_request is None:
            id_ = (str(issue.number), repo_lts)
        else:
            # add PR into index
            key_phrases = self._try_match_keywords(issue.body)
            for key_phrase in key_phrases:
                self.prs_index.add(repo, repo_lts, issue.as_pull_request(), key_phrase)
        return id_

    def _try_match_keywords(self, body):
        """Try to find keywords in issue's body.

        Args:
            body (str): Issue's body.

        Returns: List of key phrases with issue numbers, if found.
        """
        result = []
        if body:
            for pattern in PATTERNS:
                result += pattern.findall(body)
        return result
