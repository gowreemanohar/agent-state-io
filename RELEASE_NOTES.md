# 0.1.0 — 9 November 2026

First standalone release of the atomic I/O utility extracted from the maintainer's local research application. The utility implementation is unchanged; packaging, documentation, synthetic tests, and an example were added for this release. No private repository history or runtime data is included.

Verified on Windows with Python 3.13.3:

- Seven unittest tests pass, including competing processes, timeout/reacquisition, serialization failure, and replacement failure.
- Local wheel build and installation succeed.
- Installed-package counter example succeeds.

POSIX execution has not been verified in this release. This is a new public package; no external adoption or performance claims are made.
