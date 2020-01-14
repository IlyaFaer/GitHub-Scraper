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

    def update_config(self, in_repo_names):
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
