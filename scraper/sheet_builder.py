"""
Utils for reading data from GitHub and building
them into convenient structures.
"""
import datetime
import logging
from github import Github
from pr_index import PullRequestsIndex
from utils import try_match_keywords, parse_url, log_progress


class SheetBuilder:
    """Builds table of issues/PRs of the specified repos.

    SheetBuilder should be used only for the single one
    specific sheet, meaning all of the repositories set
    to be tracked by this builder, will be shown on this sheet.
    """

    def __init__(self):
        self._repos = {}  # repos tracked by this builder
        self._repo_names = {}
        # time and id of the issues last updated in the repos
        self._last_issue_updates = {}
        # dict in which we aggregate all of the issue objects
        # used to avoid re-reading unupdated issues from GitHub
        self._issues_index = {}
        self._gh_client = self._login_on_github()

        self.prs_index = PullRequestsIndex()
        self.first_update = True

    def retrieve_updated(self):
        """Build list of issues/PRs from the given repositories.

        If this is the first update, than retrieve all of the
        opened issues. If update is subsequent, than only issues
        (opened and closed), which were updated since the last
        update, will be processed.

        Returns:
            dict:
                Issues index in format:
                {issue.html_url: github.Issue.Issue}
        """
        is_first_update = False
        updated_issues = {}

        for repo_name in self._repo_names.keys():
            repo = self._repos.setdefault(
                repo_name, self._gh_client.get_repo(repo_name)
            )
            self.prs_index.index_closed_prs(repo)

            is_first_update = self._is_first_update(repo_name)

            # process issues of the repo
            issues = repo.get_issues(**self._build_filter(repo_name))
            logging.info("{repo}: processing issues".format(repo=repo.full_name))

            for index, issue in enumerate(issues):
                # "since" filter returns the issue, which was
                # the last updated in previous filling - skip it
                if (
                    issue.updated_at == self._last_issue_updates[repo_name][0]
                    and issue.html_url == self._last_issue_updates[repo_name][1]
                ):
                    continue

                self._process_issue(issue, updated_issues)

                if issue.updated_at > self._last_issue_updates[repo_name][0]:
                    self._last_issue_updates[repo_name] = (
                        issue.updated_at,
                        issue.html_url,
                    )

                log_progress(is_first_update, issues.totalCount, index, "issues")

            logging.info("{repo}: issues processed".format(repo=repo.full_name))

        self._issues_index.update(updated_issues)
        return updated_issues

    def get_from_index(self, issue_id):
        """Get issue object saved in internal index.

        Args:
            issue_id (str): Issue HTML URL.

        Returns:
            github.Issue.Issue: Issue object from index.
        """
        return self._issues_index.get(issue_id)

    def delete_from_index(self, issue_id):
        """Delete issue from internal index.

        Args:
            issue_id (str): Issue HTML URL.
        """
        if issue_id in self._issues_index.keys():
            self._issues_index.pop(issue_id)

    def read_issue(self, id_):
        """Read issue by it's URL.

        Args:
            id_ (str): Issue HTML URL.

        Returns:
            github.Issue.Issue: Issue object from GitHub.
        """
        repo_name, issue_num = parse_url(id_)
        repo = self._repos.get(repo_name)
        if not repo:
            return

        issue = repo.get_issue(int(issue_num))
        self._issues_index[issue.html_url] = issue

        if issue.updated_at > self._last_issue_updates[repo_name][0]:
            self._last_issue_updates[repo_name] = (issue.updated_at, issue.html_url)

        return issue

    def reload_config(self, config):
        """Update builder's configurations - list of tracked repos.

        Args:
            config (dict): Dict with sheet configurations.
        """
        self._repo_names = config["repo_names"]

    def get_related_prs(self, issue_id):
        """Return pull requests of the specified issue.

        Args:
            issue_id (tuple): Issue number and repo short name.

        Returns:
            list:
                All of the pull requests related to the
                specified issue.
        """
        return self.prs_index.get_related_prs(issue_id)

    def _is_first_update(self, repo_name):
        """Check if the is the first repo update.

        If True, add init date into updates index.

        Args:
            repo_name (str): Repository name.

        Returns:
            bool:
                True, if this is the first repo update,
                False otherwise.
        """
        if repo_name not in self._last_issue_updates.keys():
            self._last_issue_updates[repo_name] = (datetime.datetime(1, 1, 1), "")
            return True
        return False

    def _build_filter(self, repo_name):
        """Build filter for get_issue() call.

        Args:
            repo_name (str):
                Name of the repo, which issues we're going to request.

        Returns:
            dict: Filter, ready to be passed into the method.
        """
        args = {}
        if self._last_issue_updates[repo_name][1]:
            # if it isn't the first get-issues request, than
            # we're adding sorting and "since" filter
            # to get only recently updated issues
            args = {
                "sort": "updated",
                "direction": "desc",
                "since": self._last_issue_updates[repo_name][0],
                "state": "all",
            }
        return args

    def _login_on_github(self):
        """Authenticate on GitHub."""
        with open("loginpas.txt") as login_file:
            login, password = login_file.read().strip().split("/")

        return Github(login, password)

    def _process_issue(self, issue, updated_issues):
        """If issue is PR, indexate it. Add into updated index otherwise.

        Args:
            issue (github.Issue.Issue): Issue object.
            updated_issues (dict): Updated issues index.
        """
        if issue.pull_request is None:
            updated_issues[issue.html_url] = issue
            return

        # issue is pull request - indexate it
        for key_phrase in try_match_keywords(issue.body):
            self.prs_index.add(
                issue.repository.html_url, issue.as_pull_request(), key_phrase
            )
