# Publish this feature branch for review

The GitHub repository already exists at [bremajobs2017-lang/open-trust-standards-skills](https://github.com/bremajobs2017-lang/open-trust-standards-skills). Do not create a repository or replace its remote.

This QA task authorizes a local commit only. Obtain the owner's approval before pushing or opening a PR. After approval, confirm the current folder is `open-trust-standards-skills` and the current branch is `feat/v0.2-qa-hardening`. In Source Control, use **Publish Branch** (or **Push** if an upstream already exists) and select the existing `origin`. Complete GitHub sign-in if prompted. Do not use **Publish to GitHub**, which is the repository-creation workflow.

With approval and the GitHub Pull Requests and Issues extension installed, run **GitHub Pull Requests: Create Pull Request**. Select the existing repository, base `main`, and compare `feat/v0.2-qa-hardening`. Review the changed files, use the prepared [PR description](pull-request.md), and create the pull request. Wait for CI and human review; do not enable automatic merge as part of this task.

These steps follow [VS Code's official GitHub guidance](https://code.visualstudio.com/docs/sourcecontrol/github). Interface labels can vary by installed version and extension availability.

After approval, equivalent publication is `git push -u origin feat/v0.2-qa-hardening`. This is a normal push, never a force-push. No branch publication or PR creation is implied by these instructions; inspect the remote to confirm the actual state. Do not tag or publish a release as part of this QA task.
