# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Add `dtype` selection for physical samples through the public `Reader` API
  ([issue #148](https://github.com/BEL-Public/mffpy/issues/148)).

### Changed
- Reduce temporary allocations when calibrating physical samples
  ([issue #148](https://github.com/BEL-Public/mffpy/issues/148)).

### Fixed
- Preserve unknown `PNSSet` sensor properties as raw strings during parsing and
  serialization instead of raising `KeyError` ([#145]).
- Preserve unknown patient-field data types as raw values instead of raising
  `KeyError` ([#132]).
- Accept `os.PathLike` inputs in the `XML.from_file` type annotation
  ([issue #149](https://github.com/BEL-Public/mffpy/issues/149)).
- Correct the method name in `Reader.get_physical_samples_from_epoch` examples
  ([issue #147](https://github.com/BEL-Public/mffpy/issues/147)).

## [0.11.0] - 2026-06-03

### Added
- Add the `block_sample_counts` public property to `RawBinFile` and `Reader`
  ([#134]).

### Changed
- Add project URLs to `setup.py` ([#127]).
- Update compatibility and CI coverage for Python 3.8 through 3.11 and current
  NumPy releases ([#129], [#136]).
- Modernize GitHub Actions runners and dependencies, allow manual workflow
  runs, and skip draft pull requests ([#136], [#140]).

### Fixed
- Allow float-formatted numeric values in `PNSSet` sensor fields ([#135]).
- Handle sub-microsecond timestamps in `_parse_time_str` ([#133]).
- Correct optional-argument annotations throughout the reader APIs, including
  the calibration setter ([#129], [#136]).

## [0.10.0] - 2024-07-05
### Added
- coordinates and sensor layout XML files for 10-20 layout

### Changed
- update GHW130 3D coordinates using latest sensornet version

## [0.9.0] - 2024-03-26
### Added
- PNSSet class for parsing and writing `pnsSet.xml` files

### Fixed
- add ampSerialNumber and ampFirmwareVersion props to `FileInfo` class

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

[Unreleased]: https://github.com/bel-public/mffpy/compare/v0.11.0...HEAD
[0.11.0]: https://github.com/bel-public/mffpy/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/bel-public/mffpy/compare/v0.9.0...v0.10.0
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

[#145]: https://github.com/BEL-Public/mffpy/pull/145
[#140]: https://github.com/BEL-Public/mffpy/pull/140
[#136]: https://github.com/BEL-Public/mffpy/pull/136
[#135]: https://github.com/BEL-Public/mffpy/pull/135
[#134]: https://github.com/BEL-Public/mffpy/pull/134
[#133]: https://github.com/BEL-Public/mffpy/pull/133
[#132]: https://github.com/BEL-Public/mffpy/pull/132
[#129]: https://github.com/BEL-Public/mffpy/pull/129
[#127]: https://github.com/BEL-Public/mffpy/pull/127
