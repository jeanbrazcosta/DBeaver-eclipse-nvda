# Changelog - DBeaver Eclipse NVDA Add-on

## [2025.1] - 2025-12-20

### About This Fork
This is a modernized fork of the [original Eclipse Enhance addon](https://github.com/albzan/eclipse-nvda) by Alberto Zanella, enhanced specifically for DBeaver support.

**Maintainer:** Jean Braz <jeanbrazcosta@gmail.com>  
**Repository:** https://github.com/jeanbrazcosta/DBeaver-eclipse-nvda

### Updated
- **Updated NVDA compatibility to version 2025.3**
  - The add-on is tested with NVDA 2025.3
  - Minimum NVDA requirement remains 2021.1
  - Fully compatible with recent NVDA versions

### Improved
- **Code Quality and Modern Practices**
  - Added comprehensive type hints for better IDE support and code maintainability
  - Improved docstrings with detailed descriptions for all methods and functions
  - Replaced bare except clauses with specific exception handling
  - Better error logging with `logging` module for debugging
  - Removed redundant OLD_BEHAVIOR flag and eclipse_legacy.py dependency
  - All code now uses modern NVDA API from the current base Eclipse app module

- **Sound Handling**
  - Refactored sound playing into unified `_play_sound()` method
  - Added error handling for missing sound files
  - Improved logging when sound files cannot be found
  - Sound methods now with proper documentation

- **Text Color Detection**
  - Fixed RGB color constant format (was using incorrect hex format)
  - Added proper exception handling in color detection logic
  - Better variable names (RGB_BREAKPOINT instead of RGB_BP, RGB_WARNING instead of RGB_WARN)

- **Event Handling**
  - Improved error handling in focus events with try-except blocks
  - Better logging of errors in event processing
  - More robust caret event handling

- **Script Decorators**
  - All gesture bindings now use modern `@script` decorator
  - Consistent category naming for input gestures settings
  - Proper descriptions for accessibility

- **Console Button Handling**
  - Improved error handling when searching for and clicking console buttons
  - Better logging for debugging button click issues
  - More robust button detection in toolbar

### Fixed
- Removed OLD_BEHAVIOR configuration flag - code now always uses modern NVDA behavior
- Fixed RGB color constants format from `'rgb(2550128)'` to `'rgb(255, 0, 128)'`
- Improved error messages in braille output

### Removed
- Removed support for NVDA versions before 2021.1
- Removed OLD_BEHAVIOR flag and related legacy code path
- Removed dependency on eclipse_legacy.py (no longer needed)

### Technical Details
- Python 3.7+ required (modern NVDA requirement)
- Updated all imports to use built-in NVDA modules
- Proper type annotations for better IDE support
- Comprehensive error logging throughout the add-on
- Documentation strings for all public methods

---

## Previous Version Information
For information about versions prior to 2025.1, please refer to the git history.
