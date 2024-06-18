from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from dulwich.repo import Repo
from tests.helpers import MOCK_DEFAULT_GIT_REVISION

from poetry.packages.direct_origin import _get_package_from_git
from poetry.vcs.git.backend import Git
from poetry.vcs.git.backend import annotated_tag
from poetry.vcs.git.backend import is_revision_sha
from poetry.vcs.git.backend import urlpathjoin


VALID_SHA = "c5c7624ef64f34d9f50c3b7e8118f7f652fddbbd"

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def git_mock(mocker: MockerFixture) -> None:
    repo = MagicMock(spec=Repo)

    repo.get_config.return_value.get.return_value = (
        b"https://github.com/python-poetry/poetry.git"
    )

    repo.head.return_value = MOCK_DEFAULT_GIT_REVISION.encode("utf-8")

    # Clear any cache in the Git module
    _get_package_from_git.cache_clear()

    return repo


def test_invalid_revision_sha() -> None:
    result = is_revision_sha("invalid_input")
    assert result is False


def test_valid_revision_sha() -> None:
    result = is_revision_sha(VALID_SHA)
    assert result is True


def test_invalid_revision_sha_min_len() -> None:
    result = is_revision_sha("c5c7")
    assert result is False


def test_invalid_revision_sha_max_len() -> None:
    result = is_revision_sha(VALID_SHA + "42")
    assert result is False


@pytest.mark.parametrize(
    ("url"),
    [
        "git@github.com:python-poetry/poetry.git",
        "https://github.com/python-poetry/poetry.git",
        "https://github.com/python-poetry/poetry",
        "https://github.com/python-poetry/poetry/",
    ],
)
def test_get_name_from_source_url(url: str) -> None:
    name = Git.get_name_from_source_url(url)
    assert name == "poetry"


@pytest.mark.parametrize(("tag"), ["my-tag", b"my-tag"])
def test_annotated_tag(tag: str | bytes) -> None:
    tag = annotated_tag("my-tag")
    assert tag == b"my-tag^{}"


def test_get_remote_url(git_mock) -> None:
    repo = git_mock

    assert Git.get_remote_url(repo) == "https://github.com/python-poetry/poetry.git"


def test_get_revision(git_mock) -> None:
    repo = git_mock
    assert Git.get_revision(repo) == MOCK_DEFAULT_GIT_REVISION


def test_info(git_mock) -> None:
    repo = git_mock
    info = Git.info(repo)

    assert info.origin == "https://github.com/python-poetry/poetry.git"
    assert (
        info.revision == MOCK_DEFAULT_GIT_REVISION
    )  # revision already mocked in helper


@pytest.mark.parametrize(
    "url, expected_result",
    [
        ("ssh://git@github.com/org/repo", "ssh://git@github.com/other-repo"),
        ("ssh://git@github.com/org/repo/", "ssh://git@github.com/org/other-repo"),
    ],
)
def test_urlpathjoin(url: str, expected_result: str) -> None:
    path = "../other-repo"
    result = urlpathjoin(url, path)
    assert result == expected_result
