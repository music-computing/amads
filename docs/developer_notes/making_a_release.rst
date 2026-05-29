Making a release
================

To make a release, follow these steps:

1. Decide on the version number.
   See `Semantic Versioning <https://semver.org/>`_ for guidance.
   Briefly, the version number is of the form ``X.Y.Z`` where:

   - ``X`` is the major version number,
   - ``Y`` is the minor version number,
   - ``Z`` is the patch version number.

   The major version number should be incremented when you make incompatible API changes.
   The minor version number should be incremented when you add backwards-compatible functionality.
   The patch version number should be incremented when you make backwards-compatible bug fixes.

   For example, if the current version is ``0.1.0`` and you have made some backwards-compatible bug fixes,
   you would increment the patch version to ``0.1.1``.

2. Update the version number in the ``pyproject.toml`` file.

3. Commit the changes and push them to the ``main`` branch.

4. Create a new tag for the release as follows (replace ``0.1.1`` with the new version number):

   .. code-block:: sh

      git tag v0.1.1

5. Push the tag to the remote repository:

   .. code-block:: sh

      git push origin v0.1.1

6. GitHub Actions will automatically build the distribution and publish it to PyPI.
   You can view the progress of the release in the "Actions" tab of the GitHub repository.
   Once the release is complete, you should be able to see the release on PyPI:
   https://pypi.org/project/amads/#history.

Once the package is more mature, we should additionally maintain a changelog
that lists what changes have been made in the latest version.
