"""
Utils for reading data from GitHub and building
them into structures.
"""
import datetime
from github import Github
from const import YELLOW_RAPS, PINK, PURPLE, PATTERNS


# authenticate in GitHub
with open("loginpas.txt") as login_file:
    login, password = login_file.read().split("/")

gh_client = Github(login, password)


class SheetBuilder:
    """Class that builds table of issues/PRs from specified repos."""

    def __init__(self, sheet_id):
        self._repos = {}
        self._repo_names = {}
        self._in_repo_names = {}
        self._repo_names_inverse = {}
        self._internal_repos = []
        self._team = []
        self._sheet_id = sheet_id
        # time when any PR was last updated in specific repo
        self._last_pr_updates = {}
        self.prs_index = {}
        self.internal_prs_index = {}

    def build_table(self):
        """Build list of issues/PRs from given repositories.

        Returns:
            dict:
                Index of issue in format:
                {(issue.number, repo_short_name): github.Issue.Issue}
        """
        issue_index = {}
        repo_names = list(self._repo_names.keys()) + list(self._in_repo_names.keys())

        for repo_name in repo_names:
            repo = self._get_repo(repo_name)
            self._index_closed_prs(repo)

            # process open PRs and issues
            for issue in repo.get_issues():
                id_ = self._build_issues_id(issue, repo)
                if id_:
                    issue_index[id_] = issue

        return issue_index

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
        return repo.get_issue(int(issue_num))

    def update_config(self, config):
        """Update builder's configurations.

        Args:
            config (dict): Dict with sheet's configurations.
        """
        self._repo_names = config["repo_names"]
        self._in_repo_names = config.get("internal_repo_names", {})

        self._internal_repos = list(self._in_repo_names.keys())

        self._repo_names_inverse = dict((v, k) for k, v in self._repo_names.items())
        self._team = config["team"]

    def get_prs(self, issue_id):
        """Return internal and public pull requests of specified issue.

        Args:
            issue_id (tuple): Issue's number and repo short name.

        Returns:
            dict:
                All of the internal and public pull requests
                related to the specified issue.
        """
        prs = {}

        prs["public"] = self.prs_index.get(issue_id, [])
        prs["public"].sort(key=sort_pull_requests, reverse=True)

        prs["internal"] = self.internal_prs_index.get(issue_id, [])
        prs["internal"].sort(key=sort_pull_requests, reverse=True)

        return prs

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

        On the spreadsheet only the last PR will be shown.

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
        if repo.full_name in self._internal_repos:
            issue_num = key_exp.split()[1]
            if not (issue_num, repo_lts) in self.internal_prs_index:
                self.internal_prs_index[issue_num, repo_lts] = []

            self._add_or_update_pr(self.internal_prs_index[issue_num, repo_lts], lpr)
        # public PR
        else:
            issue_num = key_exp.split("#")[1]
            if not (issue_num, repo_lts) in self.prs_index:
                self.prs_index[issue_num, repo_lts] = []

            self._add_or_update_pr(self.prs_index[issue_num, repo_lts], lpr)

    def _add_or_update_pr(self, prs, pr):
        """Update PR in index or add it into index.

        Args:
            prs (list): PRs related to a concrete issue.
            pr (github.PullRequest.PullRequest): Recently updated PR.
        """
        is_old = False

        for index, old_pr in enumerate(prs):
            if old_pr.number == pr.number:
                prs[index] = pr
                is_old = True
                break

        if not is_old:
            prs.append(pr)

    def _get_repo_lts(self, repo):
        """Get repo's short name.

        Args:
            repo (github.Repository.Repository):
                Repository object.

        Returns:
            str: Repo's short name.
        """
        repo_lts = self._repo_names.get(repo.full_name)
        if repo_lts is None:
            repo_lts = self._in_repo_names.get(repo.full_name)

        return repo_lts

    def _index_closed_prs(self, repo):
        """Add closed pull requests into PRs index.

        Method remembers last PR's update time and doesn't
        indexate PRs which weren't updated since last
        spreadsheet update.

        Args:
            repo (github.Repository.Repository):
                Repository object.
        """
        pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
        if pulls.totalCount:
            for pull in pulls:
                if pull.updated_at < self._last_pr_updates.setdefault(
                    repo.full_name, datetime.datetime(1, 1, 1)
                ):
                    break

                key_phrases = self._try_match_keywords(pull.body)
                for key_phrase in key_phrases:
                    self._add_into_index(
                        repo, self._get_repo_lts(repo), pull, key_phrase
                    )

            self._last_pr_updates[repo.full_name] = pulls[0].updated_at

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
                self._add_into_index(
                    repo, repo_lts, issue.as_pull_request(), key_phrase
                )
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


def sort_pull_requests(pull_request):
    """Sort pull requests by their creation date."""
    return pull_request.created_at


def designate_status_color(pull, team):
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
    elif pull.user.login not in team:
        status = YELLOW_RAPS

    return status
