"""
Module which contains functions for PR processing
and indexating.
"""
import datetime
import logging
from utils import (
    try_match_keywords,
    log_progress,
    load_update_stamps,
    save_update_stamps,
)


class PullRequestsIndex(dict):
    """Pull requests index.

    Index is built this way:
        <issue URL>:
            [<PR related to this issue>, <PR related to this issue>...]

    Args:
        sheet_name (str):
            Name of the sheet, for which
            this index is assumed to be used.
    """

    def __init__(self, sheet_name):
        super().__init__()
        self._sheet_name = sheet_name
        # time when any PR was last updated in specific repo
        self._last_pr_updates = load_update_stamps("last_pr_updates", sheet_name)

    def get_related_prs(self, issue_id):
        """Get PRs related to the given issue.

        Args:
            issue_id (str): Issue URL.

        Returns:
            list: Related PRs objects.
        """
        prs = self.get(issue_id, [])
        prs.sort(key=sort_pull_requests, reverse=True)
        return prs

    def index_closed_prs(self, repo, repo_names):
        """Add closed pull requests into index.

        Method remembers last PR's update time and doesn't
        indexate PRs which weren't updated since the last
        spreadsheet update.

        Args:
            repo (github.Repository.Repository): Repository object.
            repo_names (tuple): All tracked repos names.
        """
        pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")

        if pulls.totalCount:
            is_first_update = False
            logging.info("{repo}: indexing pull requests".format(repo=repo.full_name))

            for index, pull in enumerate(pulls):
                if repo.full_name not in self._last_pr_updates.keys():
                    self._last_pr_updates[repo.full_name] = datetime.datetime(1, 1, 1)
                    is_first_update = True

                if pull.updated_at < self._last_pr_updates[repo.full_name]:
                    break

                for key_phrase in try_match_keywords(pull.body, repo_names):
                    self.add(repo.html_url, pull, key_phrase)

                log_progress(is_first_update, pulls.totalCount, index, "pull requests")

            self._last_pr_updates[repo.full_name] = pulls[0].updated_at
            logging.info(
                "{repo}: all pull requests indexed".format(repo=repo.full_name)
            )

    def save_updates(self):
        """Save last PRs update timestamps into file."""
        save_update_stamps("last_pr_updates", self._sheet_name, self._last_pr_updates)

    def add(self, repo_url, lpr, key_exp):
        """Add PR object into index or update it."""
        issue_num = key_exp.split("#")[1]

        if "/" in key_exp:  # external repo
            repo_name = key_exp.split()[1].split("#")[0]
            repo_url = "https://github.com/" + repo_name

        issue_url = repo_url + "/issues/" + issue_num
        if issue_url not in self:
            self[issue_url] = []

        self._add_or_update_pr(self[issue_url], lpr)

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
                return

        if not is_old:
            prs.append(pr)


def sort_pull_requests(pull_request):
    """Sort pull requests by their creation date."""
    return pull_request.created_at
