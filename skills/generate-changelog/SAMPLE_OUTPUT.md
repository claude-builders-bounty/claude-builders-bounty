# Changelog

## [Unreleased]

> Comparing jq-1.8.2rc1...HEAD


### Fixed
- Fix CI to add `artifact-metadata` permission for actions/attest (#3530)

### Other
- Reject numeric literals longer than DEC_MAX_DIGITS (999999999)
- Limit recursive object merge depth to prevent stack overflow
- Avoid stack overflow when freeing deeply nested values

