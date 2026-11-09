# Contributing

Install from a checkout with `python -m pip install .`, then run
`python -m unittest discover -s tests -v`. CI runs on Windows, Linux, and macOS
with Python 3.10 and 3.13. Check the actual Actions results for tested commits.

For bugs, include your OS, Python version, filesystem type, a minimal synthetic
reproduction, expected behavior, and actual behavior. Never include credentials
or production state. For changes, explain the use case and include regression
tests. Keep the runtime standard-library-only and preserve existing API behavior.

Useful contributions include testing network-filesystem limitations, documenting
integration experiences, and improving timeout semantics. Discuss API changes in
an issue before implementing them. No response-time commitment is promised.

If you use this package, you may share a public integration link in an issue.
Only independently verifiable examples should be listed as external usage.
