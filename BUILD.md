# Build Instructions for Eclipse Enhance NVDA Add-on

## Prerequisites
- Python 3.7 or later
- SCons (build tool)
- NVDA development environment

## Installation of Build Dependencies

### Using pip
```bash
pip install scons
```

### Windows (with virtual environment)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install scons
```

## Building the Add-on

### Basic Build
```bash
scons
```

This will create an `.nvda-addon` file in the current directory.

### Clean Previous Build
```bash
scons -c
```

This removes all generated files.

### Clean and Rebuild
```bash
scons -c
scons
```

## Directory Structure
```
eclipse-nvda/
├── addon/                 # Add-on source code
│   ├── appModules/       # Application-specific modules
│   │   ├── eclipse.py    # Enhanced Eclipse support
│   │   └── eclipse_legacy.py  # (Legacy - no longer used)
│   ├── doc/              # Documentation
│   │   └── en/           # English documentation
│   │   └── es/           # Spanish documentation
│   ├── locale/           # Translations
│   │   └── es/           # Spanish translations
│   ├── sounds/           # Audio files
│   └── manifest.ini      # Add-on manifest
├── site_scons/           # SCons build configuration
├── buildVars.py          # Build variables
├── sconstruct            # SCons build script
└── pyrightconfig.json    # Static analysis configuration
```

## Building with Custom Variables

You can override build variables on the command line:

```bash
scons addon_version=2025.1.1
```

## Installation for Testing

1. Build the add-on:
   ```bash
   scons
   ```

2. Rename the built file if needed:
   ```bash
   ren eclipseEnhance-2025.1.nvda-addon eclipseEnhance-2025.1.0.nvda-addon
   ```

3. In NVDA, go to:
   - Tools → Manage add-ons
   - Click "Install..."
   - Select the `.nvda-addon` file

4. Restart NVDA to activate the add-on

## Development and Testing

### Running Python Syntax Check
```bash
python -m py_compile addon/appModules/eclipse.py
```

### Type Checking with Pyright
```bash
pyright addon/
```

### Building Documentation
The documentation is generated from the source files in `addon/doc/`.

## Troubleshooting Build Issues

### 1. "scons not found"
Install SCons using pip:
```bash
pip install scons
```

### 2. "SyntaxError in addon"
Check Python version and syntax:
```bash
python -m py_compile addon/appModules/eclipse.py
```

### 3. "Missing dependencies"
Ensure you have:
- Python 3.7+
- SCons installed
- NVDA source available (for some builds)

## Release Process

1. Update version in:
   - `addon/manifest.ini`
   - `buildVars.py`
   - `2024.1.0.json` (rename if version changes)

2. Update CHANGELOG.md

3. Build the add-on:
   ```bash
   scons -c
   scons
   ```

4. Test thoroughly with multiple NVDA versions

5. Create a release on GitHub with the built `.nvda-addon` file

## Further Information

- [NVDA Development Guide](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html)
- [SCons Documentation](https://scons.org/documentation.html)
- [Eclipse IDE Accessibility](https://www.eclipse.org/eclipse/development/accessibility/)
