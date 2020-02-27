"""
Module which contains functions for PR processing
and indexating.
"""
import datetime
import logging
from utils import try_match_keywords


class PullRequestsIndex(dict):
    """Pull requests index.

    Index is built this way:
        <issue URL>:
            [<PR related to this issue>, <PR related to this issue>...]
    """

    def __init__(self):
        super().__init__()
        # time when any PR was last updated in specific repo
        self._last_pr_updates = {}

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

    def index_closed_prs(self, repo):
        """Add closed pull requests into index.

        Method remembers last PR's update time and doesn't
        indexate PRs which weren't updated since the last
        spreadsheet update.

        Args:
            repo (github.Repository.Repository): Repository object.
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

                for key_phrase in try_match_keywords(pull.body):
                    self.add(repo.html_url, pull, key_phrase)

                if is_first_update and pulls.totalCount > 1600:
                    if (index + 1) % 400 == 0:
                        logging.info(
                            "processed {num} of {total} pull requests".format(
                                num=index + 1, total=pulls.totalCount
                            )
                        )
            self._last_pr_updates[repo.full_name] = pulls[0].updated_at
            logging.info(
                "{repo}: all pull requests indexed".format(repo=repo.full_name)
            )

    def add(self, repo_url, lpr, key_exp):
        """Add PR object into index or update it."""
        issue_num = key_exp.split("#")[1]
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
