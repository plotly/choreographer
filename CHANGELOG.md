# choreographer changelog

For more context, please read through the
[release notes](https://github.com/plotly/choreographer/releases).

To see all merged commits on the main branch that will be part of the next
choreographer release, go to:

<https://github.com/plotly/choreographer/compare/vX.Y.Z...main>

where X.Y.Z is the semver of the most recent choreographer release.


## [Unreleased]

### Fixed
- Improve platform architecture detection for arm on Linux and Windows [[#290](https://github.com/plotly/choreographer/pull/290)], with thanks to @juliabeliaeva for the contribution!
- Fix license file and add a valid SPDX identifier to project settings [[#294](https://github.com/plotly/choreographer/pull/294)], with thanks to @ecederstrand for the contribution!


## [1.3.0] -- 2026-04-28

Rolls up the changes from the `1.3.0rc0`–`1.3.0rc2` release candidates.


## [1.3.0rc2] -- 2025-12-10

### Added
- Add `--verify_local` option in `choreo_diagnose` [[#288](https://github.com/plotly/choreographer/pull/288)]

### Fixed
- Check path validity for browser with `is_file()` [[#288](https://github.com/plotly/choreographer/pull/288)]
- Fix local reporting logic in `choreo_diagnose` [[#288](https://github.com/plotly/choreographer/pull/288)]


## [1.3.0rc1] -- 2025-11-30

### Changed
- Look for both the old download path and the new download path when locating chrome [[#286](https://github.com/plotly/choreographer/pull/286)]


## [1.3.0rc0] -- 2025-11-26

### Added
- Add `with_perf` keyword argument to `Session.send_command` / `Target.send_command` to return timing information about browser write/read [[#271](https://github.com/plotly/choreographer/pull/271)]
- Add a set of helper functions to await tab loading and send JavaScript [[#279](https://github.com/plotly/choreographer/pull/279)]
- Add `force` argument so chrome is not re-downloaded if the requested version already exists [[#277](https://github.com/plotly/choreographer/pull/277)]

### Changed
- Switch to a process group for more reliable termination of multi-process chrome [[#280](https://github.com/plotly/choreographer/pull/280)]
- Update default chrome from 135.0.7011.0/1418433 to 144.0.7527.0/1544685 [[#277](https://github.com/plotly/choreographer/pull/277)]
- Change chrome download path to use the XDG cache directory [[#277](https://github.com/plotly/choreographer/pull/277)]
- Make `get_chrome` verbose output print the whole JSON response [[#277](https://github.com/plotly/choreographer/pull/277)]

### Removed
- Remove unused system inspection code [[#278](https://github.com/plotly/choreographer/pull/278)]

### Fixed
- Add a retry loop to populate targets, since newer chrome takes longer and doesn't populate targets right away [[#282](https://github.com/plotly/choreographer/pull/282), [#283](https://github.com/plotly/choreographer/pull/283)]


## [1.2.1] -- 2025-11-09

### Added
- Add Roadmap

### Changed
- Use a custom threadpool for functions that could run during shutdown. Python's stdlib threadpool isn't available during interpreter shutdown nor `atexit`, so it cannot be started or shut down during `atexit`, or relied upon at all. The custom threadpool is now used during `Browser.open()` as well as `Browser.close()`, since some use patterns invoke `open` during shutdown [[#267](https://github.com/plotly/choreographer/pull/267)]
- Improve `choreo_diagnose` [[#269](https://github.com/plotly/choreographer/pull/269)]
- Improve error messaging
- Reorganize functions internally
- Bump `logistro` dependency

### Removed
- Remove `site` directory [[#270](https://github.com/plotly/choreographer/pull/270)]


## [1.2.0] -- 2025-10-22

### Changed
- Look for several chromium variants in all OSes by default [[#243](https://github.com/plotly/choreographer/pull/243)], with thanks to @hirohira9119 for the contribution!
- Replace `ThreadPoolExecutor` with a manually managed pool so it can be used inside `atexit` via `.close()` [[#260](https://github.com/plotly/choreographer/pull/260)]
- Upgrade `logistro` to reduce side effects

### Fixed
- Delete zipfile after downloading [[#257](https://github.com/plotly/choreographer/pull/257)]


## [1.1.2] -- 2025-10-07

### Added
- Add lock to mark channel open, and an `is_ready` function that checks open/close state [[#239](https://github.com/plotly/choreographer/pull/239)]

### Changed
- Appease stricter typer


## [1.1.1] -- 2025-09-18

### Fixed
- Fix bad module access [[#250](https://github.com/plotly/choreographer/pull/250)]


## [1.1.0] -- 2025-09-17

Rolls up the changes from `1.1.0rc0` and `1.1.0rc1`.


## [1.1.0rc1] -- 2025-09-16

### Changed
- Force custom JSON encoder to use the stdlib `json` package [[#249](https://github.com/plotly/choreographer/pull/249)]


## [1.1.0rc0] -- 2025-09-16

### Added
- Add option to register a custom JSON encoder [[#244](https://github.com/plotly/choreographer/pull/244)]


## [1.0.10] -- 2025-08-21

### Fixed
- Simple typing fixes [[#241](https://github.com/plotly/choreographer/pull/241)]


## [1.0.9] -- 2025-06-10

### Changed
- Serializer now accepts unsigned ints [[#232](https://github.com/plotly/choreographer/pull/232)]
- Serializer better differentiates between `pandas` and `xarray` [[#232](https://github.com/plotly/choreographer/pull/232)]


## [1.0.8] -- 2025-05-22

### Changed
- Lower default logging verbosity [[#228](https://github.com/plotly/choreographer/pull/228)]


## [1.0.7] -- 2025-04-16

### Added
- Make the default download path public [[#227](https://github.com/plotly/choreographer/pull/227)]

### Changed
- Revert ldd strategy to documentation rather than injecting deps [[#227](https://github.com/plotly/choreographer/pull/227)]
- Move some verbose logging from `DEBUG` to `DEBUG2` [[#226](https://github.com/plotly/choreographer/pull/226)]


## [1.0.6] -- 2025-04-04

### Added
- Package chromium deps and use them if `ldd` shows they are needed [[#223](https://github.com/plotly/choreographer/pull/223)]
- Add `LDD_FAIL` env var and `--ldd_fail` flag to always fail if deps are needed [[#223](https://github.com/plotly/choreographer/pull/223)]
- Add `FORCED_PACKAGED_DEPS` env var and `--forced-packaged-deps` flag [[#223](https://github.com/plotly/choreographer/pull/223)]

### Fixed
- Fix some API bugs in `choreo_diagnose` [[#223](https://github.com/plotly/choreographer/pull/223)]


## [1.0.5] -- 2025-02-23

### Added
- Add `Browser.is_isolated()` returning whether `/tmp` is sandboxed [[#219](https://github.com/plotly/choreographer/pull/219)]


## [1.0.4] -- 2025-02-11

### Fixed
- Fetch the latest *known* chrome version, not the latest version [[#214](https://github.com/plotly/choreographer/pull/214)]


## [1.0.3] -- 2025-02-10

### Changed
- Improve logging

### Removed
- Remove many CLI commands

### Fixed
- Fix syntax to make compatible with Python 3.8 [[#200](https://github.com/plotly/choreographer/pull/200)]


## [1.0.2] -- 2025-02-10

No functional changes; noop release.


## [1.0.1] -- 2025-02-09

### Changed
- Improve error messages and add some type checking for user experience

### Fixed
- Check for future cancellation before setting, improving error handling [[#197](https://github.com/plotly/choreographer/pull/197), [#198](https://github.com/plotly/choreographer/pull/198)]


## [1.0.0] -- 2025-02-06

### Added
- Add option for whole new window in `create_tab`

### Changed
- Increase wait when checking regular close
- Decrease freeze for manual bad-close cleanup
- Improve parallelization by disabling site-per-process
- General logging improvements

### Fixed
- Squash race condition
