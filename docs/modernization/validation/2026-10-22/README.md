# Retained validation evidence

`matrix/` holds the first seven serial GISTIC runs. `summary.json` and per-case
`result.json` preserve the initial filename-validator failure; `review.json`
re-evaluates unchanged outputs after that validator fix. `run.log` is complete
combined stdout/stderr for each case. Output hashes permit comparison without
committing large MAT files, caches, plots, Runtime components or downloaded binaries.

`portable-tests.log` records local unit tests. `stale-binary.log` records the
independent 7.14 versus 8.3 loader mismatch. `build-attempt.log` records the
missing licensed MATLAB prerequisite. No unavailable test is called passed.

The repeat original/off/single measurements and first unrestricted GenePattern
comparison were observed in the execution transcript, but their raw files were
lost in a second environment reset before upload. RESULTS labels those observations
separately. They must not be mistaken for retained, independently auditable logs.
