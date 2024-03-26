# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2024-03-26
### Added
- PNSSet class for parsing and writing `pnsSet.xml` files

## [0.8.0] - 2022-10-18
### Added
- coordinates and sensor layout XML files for the Geodesic Head Web

### Fixed
- writing of categories.xml when `channelStatus` attr is `None`

## [0.7.4] - 2022-06-22
### Fixed
- lxml future warning
- Test for deprecated `Reader.flavor` method

### Changed
- Revert pin on lxml

## [0.7.3] - 2022-05-25
### Changed
- use lxml parser instead of the default xml parser

## [0.7.2] - 2022-05-05
### Added
- Overwrite option for `Writer`

## [0.7.1] - 2022-02-09
### Fixed
- error when reading from an incomplete block

## [0.7.0] - 2022-01-24
### Added
- Ability to read bad channels from infoN.xml files.
- script `mffdiff.py` to compare two MFF files

### Changed
- cache `Reader._blobs`

## [0.6.3] - 2021-05-17
### Added
- dependency Deprecated

### Changed
- deprecate property `Reader.flavor` in favor of `Reader.mff_flavor`

## [0.6.2] - 2021-02-05
### Fixed
- Remove `pip` import in `setup.py` to allow `pypi` packaging

## [0.6.1] - 2021-02-03
### Fixed
In `Reader.get_physical_samples_from_epoch()`:

- wrong output when passing `dt=0.0`; now returns empty array
- error when passing `t0 = 0, 0 < dt < 1 / sr`

## [0.6.0] - 2021-01-14
### Added
- `FileInfo` properties `acquisitionVersion`, `ampType`

### Changed
- deprecate `FileInfo` property `version` for `mffVersion`

## [0.5.9] - 2020-11-25
### Fixed
- Include license and requirements in sdist.

### Changed
- Replace circleci build with GitHub Actions lint and test workflow.

## [0.5.8] - 2020-11-17
### Added
- Ability to add multiple binary files to `mffpy.Writer` object.

### Fixed
- Disallow writing EGI-incompatible binary files.
- Allow writing binary files with 0 offset between epochs.

## [0.5.7] - 2020-11-02
### Added
- XML schemata definitions (see ".XML Files" section of README.md).
- Writing of categories.xml files.

### Changed
- Parse key elements in categories.xml files with `mffpy.xml_files.Categories` class.
- Incorporate `cached_property` dependency into `mffpy` library.

[Unreleased]: https://github.com/bel-public/mffpy/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/bel-public/mffpy/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/bel-public/mffpy/compare/v0.7.4...v0.8.0
[0.7.4]: https://github.com/bel-public/mffpy/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/bel-public/mffpy/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/bel-public/mffpy/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/bel-public/mffpy/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/bel-public/mffpy/compare/v0.6.3...v0.7.0
[0.6.3]: https://github.com/bel-public/mffpy/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/bel-public/mffpy/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/bel-public/mffpy/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/bel-public/mffpy/compare/v0.5.9...v0.6.0
[0.5.9]: https://github.com/bel-public/mffpy/compare/v0.5.8...v0.5.9
[0.5.8]: https://github.com/bel-public/mffpy/compare/v0.5.7...v0.5.8
[0.5.7]: https://github.com/bel-public/mffpy/releases/tag/v0.5.7
