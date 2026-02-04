# Changelog

All notable changes to this project will be documented in this file.

## [v0.2.0] - 2026-02-04 15:30

### Added
- **Preset Management System**: Support for creating, saving, managing, and switching between multiple API configuration presets.
- **Merge Download**: Added a feature to merge multiple Markdown files into a single file with proper separation.
- **Metadata Enhancement**: Added `tags` extraction from Bilibili API (using `/x/web-interface/view/detail`).

### Changed
- **Filename Logic**: Updated bulk download filename format to `Title_UploadDate_BVId.md` for better sorting and identification.
- **UI Improvements**:
  - Refactored API configuration to use a dropdown selector.
  - Simplified button text in the file list ("Download", "Delete").
  - Fixed selection logic in lists.
- **Robustness**: Improved metadata fetching in batch mode to handle missing titles or dates by falling back to the detail API.

### Fixed
- Fixed an issue where list selection would trigger select-all behavior.
- Fixed input fields being disabled in the configuration panel.
- Fixed persistence of the selected API preset across sessions.
