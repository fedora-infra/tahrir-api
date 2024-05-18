#!/bin/sh

# Generate a block to put in the CHANGELOG.rst file.
#
# TODO: convert the changelog to Markdown, so that the Github action can pick it up on release.
# TODO: replace this by towncrier

set -e

COMMIT_URL=https://github.com/fedora-infra/tahrir-api/commit

last_tag=$(git tag --sort=creatordate | tail -n 1)
git log ${last_tag}..HEAD --no-merges --reverse --format="- %s ([%h](${COMMIT_URL}/%h>))"
