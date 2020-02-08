"""
Module which contains functions for PR processing
and indexating.
"""
import datetime
from utils import try_match_keywords


class PullRequestsIndex(dict):
    """Pull requests index.

    Object represents a dict with two fields - indexes:
        internal - index for internal PRs,
        public - index for public PRs

    Indexes are built like this:
        (<issue number>, <repository short name>):
            [<PR related to this issue>, <PR related to this issue>...]
    """

    def __init__(self):
        super().__init__()
        self["internal"] = {}
        self["public"] = {}
        # time when any PR was last updated in specific repo
        self._last_pr_updates = {}

    def reload_config(self, in_repo_names):
        """Update list of internal repos.

        Args:
            in_repo_names (dict):
                Names of internal repos, retrieved from the config.
        """
        self._internal_repos = list(in_repo_names.keys())

    def get_related_prs(self, issue_id):
        """Get internal and public PRs related to the given issue.

        Args:
            issue_id (tuple): Tuple with issue number and repo short name.

        Returns:
            dict:
                Dictionary with two fields: "internal" and "public",
                each of which is a list of related PR objects.
        """
        prs = {}

        prs["internal"] = self["internal"].get(issue_id, [])
        prs["internal"].sort(key=sort_pull_requests, reverse=True)

        prs["public"] = self["public"].get(issue_id, [])
        prs["public"].sort(key=sort_pull_requests, reverse=True)
        return prs

    def index_closed_prs(self, repo, repo_lts):
        """Add closed pull requests into PRs index.

        Method remembers last PR's update time and doesn't
        indexate PRs which weren't updated since last
        spreadsheet update.

        Args:
            repo (github.Repository.Repository):
                Repository object.
            repo (str): Repo short name.
        """
        pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
        if pulls.totalCount:
            for pull in pulls:
                if pull.updated_at < self._last_pr_updates.setdefault(
                    repo.full_name, datetime.datetime(1, 1, 1)
                ):
                    break

                key_phrases = try_match_keywords(pull.body)
                for key_phrase in key_phrases:
                    self.add(repo, repo_lts, pull, key_phrase)

            self._last_pr_updates[repo.full_name] = pulls[0].updated_at

    def add(self, repo, repo_lts, lpr, key_exp):
        """Designate the proper index and add PR into it."""
        if repo.full_name in self._internal_repos:
            self._add(repo_lts, lpr, key_exp, "internal")
        else:
            self._add(repo_lts, lpr, key_exp, "public", "#")

    def _add(self, repo_lts, lpr, key_exp, key, delimeter=None):
        """Add PR object into index or update it."""
        issue_num = key_exp.split(delimeter)[1]
        if not (issue_num, repo_lts) in self[key]:
            self[key][issue_num, repo_lts] = []

        self._add_or_update_pr(self[key][issue_num, repo_lts], lpr)

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


def sort_pull_requests(pull_request):
    """Sort pull requests by their creation date."""
    return pull_request.created_at
