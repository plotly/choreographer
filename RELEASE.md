# How to release choreographer

This document describes how a maintainer publishes a new version of choreographer. The primary steps are a changelog update, a git tag, and an upload to PyPI.

## Before you start

You need the following:

- Write access to <https://github.com/plotly/choreographer>
- An account on PyPI with upload permissions for the `choreographer` project
- A PyPI API token, or membership of the `pypi` deployment environment
- `uv` on your machine
- A local clone of the repository with all tags

Get the tags with this command:

```bash
git fetch --tags
```

## How the version number works

No file in the repository holds the version number. The build backend uses `setuptools-git-versioning`, so the most recent git tag sets the version. See the `[tool.setuptools-git-versioning]` table in `pyproject.toml`.

Print the version that the current checkout produces:

```bash
uv run --no-sync --with setuptools-git-versioning setuptools-git-versioning
```

On a tagged commit, the command prints the clean version, for example `1.3.0`. On any other commit, the command prints a development version, for example `1.3.0.post22+git.4a278bc2`. PyPI rejects a development version, because the version carries a local part after the plus sign. Thus only a tagged commit produces a package that you can upload.

Tag names start with `v` and follow [semantic versioning](https://semver.org). A release candidate adds `rcN` with no separator, for example `v1.4.0rc0`.

## Step 1: Update the changelog

1. Open `CHANGELOG.md`. The file follows the [keep a changelog](https://keepachangelog.com) format.
2. Add a new section under `## [Unreleased]`, in the form `## [X.Y.Z] -- YYYY-MM-DD`
3. Move each entry out of the `[Unreleased]` section into the new section. Leave the `[Unreleased]` heading in place with no entries.
4. Keep the subsection order: `Added`, `Changed`, `Removed`, `Fixed`
5. Make sure that each entry links to the pull request or the issue

Open a pull request with this change and merge the pull request into `main`. The repository uses conventional commits, so title the pull request `chore: Update files for release of vX.Y.Z`.

## Step 2: Confirm that main is ready

1. Open the Actions tab and confirm that `test` passed on `main`
2. Make sure that `uv.lock` matches `pyproject.toml`. The release workflow runs `uv sync --locked` and fails on a stale lock file.

   ```bash
   uv lock --check
   ```

   The command exits 0 when the two files agree, and exits 1 when they do not.

3. Make sure that your working tree is clean. The release workflow fails on a dirty tree, because a dirty tree changes the version.

## Step 3: Tag the release

Tag the merge commit of your changelog pull request. The project uses lightweight tags.

> [!NOTE]
> `setuptools-git-versioning` reads a lightweight tag correctly. But plain `git describe` skips a lightweight tag and reports an older one. Pass `--tags` to see the true most recent tag.

```bash
git checkout main
git pull
git tag v1.4.0
git push origin v1.4.0
```

> [!WARNING]
> PyPI refuses a second upload of the same version. If you must correct a release that PyPI holds already, release the next version number. A tag that no package index knows is still safe to move.

## Step 4: Watch the release workflow

The tag push starts the `test-and-build` workflow in `.github/workflows/test_and_build.yml`. The single `super-test` job builds the package on Linux, Windows, and macOS, across each supported Python version. The job reinstalls the built wheel, downloads chrome, runs `choreo_diagnose`, and runs the test suite.

The workflow publishes nothing. The workflow proves that the tagged commit builds and passes on every platform.

If `super-test` fails, read the failure before you continue. A flaky browser test does not block the release, but a build failure does.

## Step 5: Publish to PyPI

The `publish-pypi` workflow in `.github/workflows/publish_pypi.yml` uploads the package. The workflow authenticates with OIDC through the `pypi` deployment environment, so no token is necessary.

1. Open the Actions tab and select `publish-pypi`
2. Select Run workflow
3. Enter the tag, for example `v1.4.0`
4. Start the run
5. Open the run and approve the deployment under Review deployments

The `pypi` environment needs a review from the `plotly/libraries_admin` team. You can approve your own run. The job waits for that approval before GitHub issues the OIDC token, so an unapproved run never reaches PyPI.

The workflow checks out the tag, builds the package, and confirms that the built version matches the tag. The upload carries `skip-existing`, so a second run of the same tag skips the files that PyPI holds already.

PyPI marks a release candidate as a pre-release, so `pip install choreographer` continues to resolve to the most recent final version.

> [!NOTE]
> To upload from your machine instead, build from a clean clone of the tag and run `uv publish` with a PyPI API token. Clear `dist/` first. `uv publish` sends every file in `dist/`, so an old artifact there fails the upload.

## Step 6: Create the GitHub release

`CHANGELOG.md` points readers to the GitHub releases page for more context.

1. Open <https://github.com/plotly/choreographer/releases/new>
2. Select the tag that you pushed
3. Use the tag name as the title
4. Paste the new `CHANGELOG.md` section as the body
5. For a release candidate, mark the release as a pre-release

## Step 7: Confirm the release

Install the package from PyPI in a clean environment:

```bash
uv run --no-project --with choreographer==1.4.0 choreo_diagnose --no-run
```

If the release changes the public API, tell the maintainers of [kaleido](https://pypi.org/project/kaleido/), which depends on choreographer.

## Current gaps

- The `testpypi` deployment environment has no purpose now. No workflow uses that environment.
- No workflow builds or deploys the documentation. The `mkdocs` dependency group in `pyproject.toml` is commented out, and `mkdocs.yml` needs the `quimeta`, `quicopy`, and `quiapi` plugins from `mkquixote`, which installs only over SSH from a private repository. A release changes no documentation site.
