import re


class GitHubSlug:
    def __init__(self, slug_string: str) -> None:
        regex = re.compile("^[^/\n]+/[^/\n]+$")
        if regex.match(slug_string):
            self.slug = slug_string
        else:
            raise ValueError(
                "The input string is not a valid GitHub slug. \
                GitHub slugs must be in the format <owner>/<repository-name>"
            )

    @property
    def repo_owner(self) -> str:
        owner, _ = self.slug.split("/")
        return owner

    @property
    def repo_name(self) -> str:
        _, repo_name = self.slug.split("/")
        return repo_name

    def __repr__(self) -> str:
        return f'GitHubSlug("{self.slug}")'

    def __str__(self) -> str:
        return self.slug
