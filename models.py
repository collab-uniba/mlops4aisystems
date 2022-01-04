import re


class GitHubSlug:
    def __init__(self, slug_string: str) -> None:
        regex = re.compile("^([^/\n]+)/([^/\n]+)$")
        match = regex.match(slug_string)
        if match:
            self.slug = slug_string
            self.repo_owner = match.group(1)
            self.repo_name = match.group(2)
        else:
            raise ValueError(
                "The input string is not a valid GitHub slug. \
                GitHub slugs must be in the format <owner>/<repository-name>"
            )

    def __repr__(self) -> str:
        return f'GitHubSlug("{self.slug}")'

    def get_repo_owner(self) -> str:
        return self.repo_owner

    def get_repo_name(self) -> str:
        return self.repo_name

    def __str__(self) -> str:
        return self.slug
