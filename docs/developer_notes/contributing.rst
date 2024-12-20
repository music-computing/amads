Contributing
============

We welcome contributions to the project! Whether you want to fix bugs, improve documentation, or add new features, here's how you can contribute:

GitHub contribution workflow
---------------------------

1. Submit a pull request
~~~~~~~~~~~~~~~~~~~~~~~

For team members
^^^^^^^^^^^^^^^

1. Create a new branch from main::

    git checkout -b feature-name

2. Make your changes and commit them
3. Push the branch::

    git push origin feature-name

4. Open a pull request from your branch to main

For external contributors
^^^^^^^^^^^^^^^^^^^^^^^

1. Fork the repository to your GitHub account
2. Clone your fork::

    git clone https://github.com/your-username/amads.git

3. Create a branch::

    git checkout -b feature-name

4. Make your changes and commit them
5. Push to your fork::

    git push origin feature-name

6. Open a pull request from your fork to our main branch


2. Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~~

All pull requests must pass our automated test suite in the CI pipeline before they can be merged. This ensures code quality and prevents regressions.

One of the tests will run the code coverage tool, which will report on the percentage of code that is covered by tests.
If you see that the coverage is low, please add tests for the code you are changing.

3. Code Review
~~~~~~~~~~~~~

A project maintainer will review your code. They may request changes or clarification. This helps maintain code quality and consistency.

The reviewers points will appear as comments on the pull request, which you can view on GitHub.
You can respond to those comments with your own comments, but in many cases you will also want to make changes to your code.
To do this, simply push more commits to your branch. The pull request will automatically update to reflect the changes.

Once you have made the required code changes for a particular discussion point,
please add a comment to the thread indicating that you have made the changes.
Do not resolve the comment yourself, as the reviewer needs to be able to check your changes.
They are the one who should resolve the comment once they are satisfied.

Once you have finished responding to all the comments, you can re-request review by clicking the "Re-request review" button
in the GitHub UI.

4. Merging
~~~~~~~~~

Once your pull request passes CI and receives approval from a reviewer, it can be merged into the main codebase.
You as author can merge it yourself, or you can ask a reviewer to merge it for you.
When merging, please use the "Squash and merge" option, which will combine all the commits into a single commit.
This helps keep the commit history clean and easy to understand.
There's one case, though, where squashing is a bad idea, and that's when someone else is working on another branch
that branched off your branch (in general we try to avoid this, but sometimes it happens!).
In this case, you should merge the pull request as a normal merge, not a squash merge.


What makes a good pull request?
-------------------------------

You can contribute many kinds of things via a pull request:

* Bug fixes
* Documentation improvements
* New features and functionality
* Test cases

When submitting pull requests, follow these guidelines:

#. Keep changes small and focused

   * Each PR should address a single concern
   * Break large changes into smaller, logical PRs
   * This makes review easier and reduces merge conflicts

#. Write clear PR descriptions

   * Explain what the changes do and why they're needed
   * Reference any related issues
   * Include before/after examples if relevant
   * List any breaking changes or dependencies

For example, instead of one large PR that adds multiple features, refactors code, and fixes bugs, break it into:

* PR 1: Add new feature X
* PR 2: Refactor module Y
* PR 3: Fix bug Z

This approach helps reviewers understand your changes and speeds up the review process.

How do I contribute a new algorithm?
------------------------------------

When contributing a new algorithm, first review existing examples in the source code to understand the project's structure and conventions.
Consider carefully where your algorithm fits in the codebase hierarchy.

When writing your code, try to follow our style guidlines. Write clear and complete documentation,
including relevant citations with DOIs/URLs where possible.

Your contribution should include comprehensive tests, including both doctests and unit tests.
See :doc:`testing` for more information.

If you haven't already, make sure you have installed the pre-commit hooks (see :doc:`style`).
The hooks will help ensure your code meets the project's formatting and style requirements.