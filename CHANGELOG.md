# Changelog

All notable changes to the program will be documented here.

### [Unreleased]

#### Added
- Began reintroduction of a logging system.
- Added some comments, more will come.
- Added warning message on data panel advising the data could be up to 5 minutes out of date with respect to the MPC, monitor page is fully up to date.
- Added loading indicators to plots on NEO page.

#### Changed
- Added a background job to periodically pull data from the MPC. Originally used an awful method involving an open route and a server cron job.
- Significant improvements to the monitor page (more functionality, such as ability to clear and restore individual updates, and easier to navigate)
- Began implementation of BEM for frontend.

#### Fixed
- Fixed the formatting of some files to be more consistent.
- Fixed an issue where simultaneous calls to fetch monitor data would create duplicate update records. Only backend can run an update now.

### [0.2.3] QOL Fixes and Changes

#### Changed
- Made a few GUI updates, specifically to the monitoring page and settings page.
- Refactored the project slightly for better organization.
- Reorganized the configuration file.
- Separated calls for table and updates section of monitor page for clarity and easier debugging.
- Reduced the time interval at which data is retrieved from APIs.

#### Fixed
- Minor typo fixes.
- Monitor page no longer does a full reload on clear.

### [0.2.2] QOL Fixes and Additions

#### Fixed

- Quick-fixed error on startup when logs dir does not exist, long term solution required.
- Updated README.md to reflect last update date.
- Fixed changelog entry to show "unreleased" instead of 0.2.2.
- Quick fix on monitor ignore/clear system.

#### Changed

- Updated name of program in `setup.py`.
- Moved update storage from memory to disk.
- Removed logging system due to unresolved errors, will be added back in the future.
- Moved ignore id list out of memory to disk.
- Removed force update selector to prevent API spam, changes update interval to 10m.
- Changed audio backend system to be more reliable.

#### Added

- Added sound system for monitoring page. A notification sound will play when there is a database update.
- Added monitor system daemon entrypoint (will potentially be changed later).

### [0.2.1] Monitor Update

#### Added

- Added monitoring panel showing real time updates to the MPC database.
- Low MOID values now blink red on the main data panel.
- Flask will now serve custom error pages.
- Other minor additions.

#### Changed

- Improved the caching system, began implementation of APICache which will be complete in a future update.
- Reorganized some files for clarity.
- Other minor changes.

#### Fixed

- Fixed a bug where instantiation of new classes for each user would occur on every call, now only occurs once per session.
- Fixed an issue with the previous cache validation system which caused the `NEOData` class dataframe update to loop several times on each call.
- Set client-side rate limits to API calls to prevent spam.
- Other minor bug fixes.

### [0.1.3] Quick Fix

#### Fixed

- Fixed instances where white text was displayed on a white background.

### [0.1.2] Error Handler

#### Added

- Added web app error handling and error page display. 

### [0.1.1] GUI Update

#### Added

- Added Monitor page. Currently work in progress.
- Created logo. Added to web page and README.

#### Changed

- Now supports light mode and dark mode. Dark mode is now darker.
- Cleaned CSS/HTML somewhat, still very dirty.
- Renamed some files for clarity.

#### Fixed

- Fixed error for corrupted NEOCP JSON cache files.

### [0.1.0] Initial Program Release

---