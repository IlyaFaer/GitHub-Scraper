"""
Utils for reading data from GitHub and building
them into convenient structures.
"""
import datetime
import logging
from github import Github
from pr_index import PullRequestsIndex
from utils import try_match_keywords, parse_url


class SheetBuilder:
    """Builds table of issues/PRs of the specified repos.

    SheetBuilder should be used only for the single one
    specific sheet, meaning all of the repositories set
    to be tracked by this builder, will be shown on this sheet.
    """

    def __init__(self):
        self._repos = {}  # repos tracked by this builder
        self._repo_names = {}
        # time when any issue was last updated in every repo
        self._last_issue_updates = {}
        self.prs_index = PullRequestsIndex()
        # dict in which we aggregate all of the issue objects
        # used to avoid re-reading unupdated issues from GitHub
        self._issues_index = {}
        self._gh_client = self._login_on_github()
        self.first_update = True

    def retrieve_updated(self):
        """Build list of issues/PRs from the given repositories.

        If this is the first update, than retrieve all of the
        opened issues. If update is subsequent, than only issues
        (opened and closed), which were updated since the last
        update will be processed.

        Returns:
            dict:
                Index of issues in format:
                {issue.html_url: github.Issue.Issue}
        """
        is_first_update = False
        updated_issues = {}

        for repo_name in self._repo_names.keys():
            repo = self._repos.setdefault(
                repo_name, self._gh_client.get_repo(repo_name)
            )
            self.prs_index.index_closed_prs(repo)

            # process issues of the repo
            issues = repo.get_issues(**self._build_filter(repo_name))
            logging.info("{repo}: processing issues".format(repo=repo.full_name))

            for index, issue in enumerate(issues):
                if repo_name not in self._last_issue_updates.keys():
                    self._last_issue_updates[repo_name] = datetime.datetime(1, 1, 1)
                    is_first_update = True

                id_ = self._build_issue_id(issue, repo)
                if id_:
                    updated_issues[id_] = issue

                self._last_issue_updates[repo_name] = max(
                    self._last_issue_updates[repo_name], issue.updated_at
                )
                # log progress if repo is too big
                if is_first_update and issues.totalCount > 1600:
                    if (index + 1) % 400 == 0:
                        logging.info(
                            "processed {num} of {total} issues".format(
                                num=index + 1, total=issues.totalCount
                            )
                        )
            logging.info("{repo}: issues processed".format(repo=repo.full_name))

        self._issues_index.update(updated_issues)
        return updated_issues

    def get_from_index(self, tracked_id):
        """Get issue object saved in internal index.

        Args:
            tracked_id (str): Issue HTML URL.

        Returns:
            github.Issue.Issue: Issue object from index.
        """
        return self._issues_index.get(tracked_id)

    def delete_from_index(self, tracked_id):
        """Delete issue from internal index.

        Args:
            tracked_id (str): Issue HTML URL.
        """
        self._issues_index.pop(tracked_id)

    def read_issue(self, url):
        """Read issue by it's number and repository short name.

        Args:
            issue_num (str): Issue number.
            repo_lst (str): Repository short name.

        Returns:
            github.Issue.Issue: Issue object from GitHub.
        """
        repo_name, issue_num = parse_url(url)
        repo = self._repos.get(repo_name)
        if not repo:
            return

        issue = repo.get_issue(int(issue_num))
        self._issues_index[issue.html_url] = issue
        return issue

    def reload_config(self, config):
        """Update builder's configurations - list of tracked repos.

        Args:
            config (dict): Dict with sheet's configurations.
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

    def _build_filter(self, repo_name):
        """Build filter for get_issue() call.

        Args:
            repo_name (str):
                Name of the repo, which issues we're going to request.

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

    def _login_on_github(self):
        """Authenticate on GitHub."""
        with open("loginpas.txt") as login_file:
            login, password = login_file.read().strip().split("/")

        return Github(login, password)

    def _build_issue_id(self, issue, repo):
        """Designate issue's id. If issue is PR, index it.

        Args:
            issue (github.Issue.Issue): Issue object.
            repo (github.Repository.Repository): Repository object.

        Returns:
            str: Issue URL.
        """
        # issue is not a pull request
        if issue.pull_request is None:
            return issue.html_url

        # issue is pull request - indexate it
        key_phrases = try_match_keywords(issue.body)
        for key_phrase in key_phrases:
            self.prs_index.add(
                issue.repository.html_url, issue.as_pull_request(), key_phrase
            )

        return ""
