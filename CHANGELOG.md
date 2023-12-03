# Changelog

All notable changes to the program will be documented here.

### [Unreleased]

#### Fixed

- Quick-fixed error on startup when logs dir does not exist, long term solution required.
- Updated README.md to reflect last update date.
- Fixed changelog entry to show "unreleased" instead of 0.2.2.

#### Changed

- Updated name of program in `setup.py`.
- Slightly improved logging for monitor system.
- Moved update storage from memory to disk.
- Removed logging system due to unresolved errors, will be added back in the future.

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