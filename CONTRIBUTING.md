# How to Contribute

First of all, thank you for putting in the time and effort to contribute to this project!

Before submitting a PR, check open issues and PRs to see if there is already someone working on the
problem.

This project relies heavily on automation for code consistency.
linearmoney is a small project without the resources to manually review things like code style, so
PRs that fail any CI checks will not be accepted, even if it's only the linter.

## Workflow

linearmoney uses [Hatch](https://hatch.pypa.io/latest/) for its tooling, so
you'll need to [install](https://hatch.pypa.io/latest/install/#pipx) it if
you haven't already.

Once you have hatch installed, you can checkout a local branch on your fork and freely
develop on the source code. Hatch takes care of virtualenv setup, so to experiment with
the project in the REPL, you can just use `hatch shell` in the project root directory.

You can also run the test suite with hatch without entering a virtualenv: `hatch run test:suite`.

The test suite is very thorough, and it should catch most, if not all, regressions that your changes introduce.
It's also very fast, generally less than 3 seconds to run the entire suite on a Ryzen 5 2600, so
running the full test suite regularly while developing is an efficient workflow.

Before submitting your changes as a PR, run the full automation suite locally with `hatch run all`.
This includes formatting (black), linting (flake8), and type checking (mypy).
Fix any local failures before pushing your changes.

## Documentation Changes

The automation suite does not build the documentation by default. This is to prevent extraneous
diffs from cluttering git status and history when nothing was actually changed.

If you are contributing documentation changes or you made a change to a docstring as part
of your code changes, you can verify the changes locally with:

```bash
hatch run docs:build
hatch run docs:serve
```

This will serve the built documentation site at `localhost:8000`.

Please do not commit the built documentation even if making documentation-specific changes.

The changes to the markdown or source files are what we want to see in the diff for documentation
updates. The documentation site will be regenerated by the maintainer when a release is prepared
or at their discretion if a correction to the current version needs to be published.

## Testing Guidelines

Test coverage is not enforced by CI or review policy, but you are strongly encouraged to add
test cases that validate your changes in the same PR. Ideally, the tests will be added with a
separate commit from the source changes to make red-green validation easier for the reviewer.

In particular, bug fixes will not be merged without a regression case to prevent reintroduction of the bug.

We want this project to be friendly to new contributors, so if you are new to
testing, feel free to ask for help from the current maintainer with an @-mention
in the PR description. They will assist you with a detailed review of your test cases, or if needed,
they can write the tests for you. However, they may request changes to the source implementation
if the code is not written in a way that is easily testable. Code that is easily testable is usually easier
to change later as well, so this is an opportunity to improve the design of the changes before
merge.

## Note on AI Generated Contributions

Please do not submit a PR that was generated by an LLM. Many people may
find LLMs very helpful for drafting their PR
descriptions or for assistance with solving some problems in code, and these
are completely valid and acceptable uses of AI. Using an AI coding
assistant or an LLM as part of your workflow is fine, but the maintainer
doesn't have the time to
review code that was generated *entirely* by an AI.

It can be difficult to tell
the difference between code generated by an AI and code that was written
by a developer who is unfamiliar with the language or the project, and it
takes time and effort to contribute to an open source project, so we will
give the benefit of the
doubt and try to help you improve the code if your contribution does not
meet the quality standards of the project. We ask that you
give the same respect of our time and effort and do not submit completely
AI-generated code. Thank you!

## Community Interactions

This project does not yet have a Code of Conduct, but interactions with
other contributors and users of the project should remain professional.

In general, anything that would not be appropriate when dealing with a
coworker or client should be considered inappropriate here as well.
