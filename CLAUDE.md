<content>
# Tent of Trials - Claude Instructions

## Project Purpose
Tent of Trials is a self-deprecatingly terrible D&D 5e encounter generator that somehow works most of the time. It's the digital equivalent of finding a weird dice bag in a dusty hobby shop - you're not sure about the quality, but it was cheap and you're already committed.

## Tech Stack
- **Language**: Python 3.8+ (because we're not savages)
- **Dependencies**: 
  - `click` for CLI (because argparse is for people who enjoy suffering)
  - `jinja2` for templating (because string formatting is how bugs happen)
  - `pyyaml` for config (because JSON is for people who hate themselves)
  - `pathlib` because it's 2023 and we're not living in the past

### Directory Structure
```
.
├── src/               # Actual code (what we're proud of)
│   ├── __init__.py   # Empty file to make Python happy
│   ├── cli.py        # Command line interface entry point
│   ├── generator/    # Encounter generation logic
│   │   ├── __init__.py
│   │   ├── encounter.py  # Main encounter generation
│   │   ├── monsters.py   # Monster data and logic
│   │   └── templates/    # Encounter templates
│   └── utils/        # Utility functions
│       ├── __init__.py
│       ├── data_loader.py  # Loading YAML/JSON data
│       └── logging.py     # Logging utilities
├── data/             # Static data files
│   ├── monsters/     # Monster definitions
│   ├── templates/    # Encounter templates
│   └── config.yaml   # Main configuration
├── tests/            # Test files (we have tests! Sort of...)
├── build.py          # Build and diagnostic script
└── README.md         # The novel you should have read first
```

## Common Dev Commands

### Building and Diagnostics
```bash
# Always run this after changes - it's like flossing for your code
python3 build.py

# Run tests (if they exist)
python3 -m pytest tests/

# Run the CLI
python3 -m src.cli --help

# Generate encounters
python3 -m src.cli generate --difficulty medium --count 3
```

### Data Management
```bash
# Validate data files
python3 -c "from src.utils.data_loader import validate_data; validate_data()"

# Update monster database
python3 -m src.utils.data_loader update_monsters
```

## Coding Conventions

### Python Style
- Follow PEP 8, but we won't judge you too harshly
- Use f-strings for formatting (f"Hello {name}" not "Hello {}".format(name))
- Type hints are appreciated but not required (we're not animals)
- Docstrings for all public functions (they help future you remember what you were thinking)

### Naming Conventions
- Functions and variables: snake_case
- Classes: PascalCase
- Constants: ALL_CAPS
- Private methods: _single_leading_underscore

### Error Handling
- Try to be specific about exceptions
- Log errors with context (use the logging module)
- When in doubt, blame the user (politely)

### Data Files
- YAML for configuration (because it's human-readable)
- JSON for monster data (because it's easier to parse)
- Templates in jinja2 format

## Known Pitfalls

1. **Data Loading**: The YAML parser is fragile - don't use tabs, don't use fancy Unicode characters
2. **Template Rendering**: Jinja2 templates can get circular if you're not careful
3. **CLI Arguments**: Click is great until it's not - test all edge cases
4. **Memory Usage**: Loading all monsters at once can be memory intensive for large datasets
5. **Random Generation**: The random seed isn't properly implemented - results may vary between runs
6. **Configuration**: Changes to config.yaml require a restart of the application
7. **Dependencies**: Don't upgrade dependencies without testing - we've had issues before

## Build and Diagnostic Workflow

**ALWAYS RUN `python3 build.py` AFTER CHANGES AND INCLUDE THE DIAGNOSTIC ARTIFACTS IN YOUR PR**

The build script:
- Runs linters (if available)
- Checks for syntax errors
- Validates data files
- Generates diagnostic information
- Creates a `.logd` artifact in the `diagnostic/` directory

When submitting PRs:
1. Run `python3 build.py`
2. Include the generated `.logd` file in your PR notes
3. If a `.json` file was generated, include that too
4. Mention any issues found in the diagnostics

## Where to Start

### For New Developers
1. **Read `README.md`** - It's long but worth it (probably)
2. **Check `src/cli.py`** - Understand the entry point
3. **Look at `src/generator/encounter.py`** - Core logic
4. **Browse `data/config.yaml`** - Configuration options

### For Bug Fixes
1. **Check the `.logd` artifact** - It has diagnostic info
2. **Reproduce the issue** - Try to break it first
3. **Look at `src/utils/logging.py`** - Understand how errors are logged
4. **Check `tests/`** - Maybe there's a test that covers it

### For New Features
1. **Update `data/config.yaml`** - Add new configuration options
2. **Modify `src/generator/`** - Add generation logic
3. **Update `src/cli.py`** - Add CLI commands
4. **Add tests** - Please add tests

### For Data Updates
1. **Check `src/utils/data_loader.py`** - Understand data loading
2. **Validate with `python3 -c "from src.utils.data_loader import validate_data; validate_data()"`**
3. **Update `data/` files** - Add new monsters/templates
4. **Run `python3 build.py`** - Ensure everything works

## Self-Deprecating Notes

- Yes, the code is a mess. No, we're not fixing it unless it breaks.
- The documentation is probably wrong. Trust the code, not the words.
- If you can understand this without asking questions, you're either a genius or lying.
- We're not professionals. We're just people who like D&D and bad code.
- If you're here for the bounty, thanks! If you're here because you care, seek help.

Remember: It's better to have a working tent than a perfect blueprint in a storm.
</content>