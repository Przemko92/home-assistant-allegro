# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code lints (using ruff: `scripts/lint`).
4. Test your contribution.
5. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

Use [ruff](https://docs.astral.sh/ruff/) to make sure the code follows the style (`scripts/lint`).

## Test your code modification

This custom component is based on [integration_blueprint template](https://github.com/ludeeus/integration_blueprint).

It comes with a Visual Studio Code / Cursor Dev Container. Reopen the folder
in the container, then run the task **Run Home Assistant on port 8123**.
Home Assistant uses [`.devcontainer/configuration.yaml`](./.devcontainer/configuration.yaml).

## Releasing (HACS)

HACS installs from GitHub **releases** (not from a git tag alone).

1. Bump `version` in `custom_components/allegro/manifest.json` and `VERSION` in `custom_components/allegro/const.py` so they match.
2. Merge to `main`.
3. Create a GitHub release whose tag equals that version (for example `0.0.6`). GitHub can generate release notes from `.github/release.yml`.
4. The **Release** workflow checks that the tag matches the manifest and attaches `allegro.zip` to the release.

Until the integration is in the HACS default store, users add this repository as a custom repository. After a successful HACS + hassfest run on `main` and a new release, submit a PR to [hacs/default](https://github.com/hacs/default) (`integration` file, alphabetical). The HACS action must pass **without** ignored checks.

GitHub repository settings that HACS also checks: a short description, issues enabled, and topics such as `hacs`, `home-assistant`, `custom-component`, `allegro`.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
