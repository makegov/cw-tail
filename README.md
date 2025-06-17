# cw-tail

**cw-tail** is a Python-based CLI tool that tails AWS CloudWatch logs and displays them in a colored, simplified two‑column layout. It's designed to help you quickly monitor log activity directly from your terminal.

## Features

- **Multiple Named Configurations:** Store different configurations for various environments or use cases in a single YAML file
- **Colored Output:** Uses ANSI escape codes to colorize output, making it easier to spot important messages
- **Flexible Filtering:** Filter, highlight, or exclude logs based on user‑specified tokens
- **Configurable Time Window:** Tail logs from a specified duration (e.g., the last 1 hour, 15 minutes, etc.)
- **Stream Name Shortening:** Automatically shortens container/log stream names for a cleaner display

## Requirements

- Python 3.12 or later
- AWS credentials configured (via environment variables, AWS CLI configuration, or IAM roles)
- [uv](https://docs.astral.sh/uv/) for Python package management

## AWS CLI Setup

- **Install AWS CLI:** Make sure the AWS CLI is installed. You can follow [these instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for installation.
- **Configure AWS Credentials:** You must have a properly configured `~/.aws/credentials` file with valid `aws_access_key_id` and `aws_secret_access_key`. For example:

  ```ini
  [default]
  aws_access_key_id = YOUR_ACCESS_KEY_ID
  aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
  ```
  
Alternatively, you can set these values as environment variables.

## Installation

### Prerequisites

First, install [uv](https://docs.astral.sh/uv/) if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Option 1: Install as a Global Tool (Recommended)

Install `cw-tail` globally using uv tool:

```bash
uv tool install cw-tail
```

Or install from the source directory:

```bash
uv tool install .
```

After installation, you may need to add uv's tool directory to your PATH:

```bash
uv tool update-shell
```

### Option 2: Development Installation

For development or if you want to modify the code:

```bash
# Clone the repository
git clone <repository-url>
cd cw-tail

# Install dependencies and create virtual environment
uv sync

# Run the tool during development
uv run cw-tail --help
```

### Development Installation

For development or local usage:

```bash
# Sync dependencies and create virtual environment
uv sync

# Run the tool
uv run cw-tail --help
```

### Global Installation

To install as a globally available tool:

```bash
# Install as a uv tool (recommended)
uv tool install .

# Then use anywhere
cw-tail --help
```

## Configuration

### Configuration File Priority

`cw-tail` looks for configuration files in the following order:

1. **`./config.yml`** (project-specific) - **Recommended for teams/projects**
2. **`./.cw-tail.yml`** (project-specific, hidden file) - Good for personal project configs
3. **`~/.config/cw-tail/config.yml`** (user-global) - Fallback for global settings

The first file found will be used. This allows you to:
- **Share configs with your team** by committing `./config.yml` to your repository
- **Keep personal configs private** by using `./.cw-tail.yml` (which is in `.gitignore`)
- **Have global defaults** in your user config directory

### Creating Configuration Files

There is an example configuration file (`config.example.yml`) in the repository. The tool will create a default global configuration if none exists. Here's an example configuration:

```yaml
default:
  region: us-east-1
  since: 1h
  colorize: true

prod:
  log_group: production-logs
  since: 10m
  highlight_tokens: [301, 302, 429, 500, error, warning, critical]
  exclude_tokens: []
  exclude_streams: []
  formatter: json_formatter
  format_options:
    remove_keys: logger
    key_value_pairs: level:info,level:debug,ip:my-ip-address

dev:
  log_group: development-logs
  since: 10m
  highlight_tokens: [429, 500, error, warning, critical]
  exclude_tokens: []
  formatter: json_formatter
  format_options:
    remove_keys: logger,request_id
    key_value_pairs: ip:my-ip-address
```

Any values provided via command‑line arguments will override these configuration values.

## Usage

### If Installed as Global Tool

```bash
cw-tail --help
```

### If Using Development Installation

```bash
uv run cw-tail --help
```

### Examples

```bash
# Use the prod configuration from local config file
cw-tail --config prod

# Use the dev configuration but override the time window
cw-tail --config dev --since 30m

# Use default configuration with a specific log group
cw-tail --log-group my-logs --colorize
```

### Project-Specific Configuration Example

For a typical project setup:

1. **Create a project config file:**
   ```bash
   # Copy the example config to your project
   cp config.example.yml config.yml
   
   # Edit it for your project's log groups and settings
   # Then commit it so your team can use the same settings
   ```

2. **Use project-specific configs:**
   ```bash
   # These will use your project's config.yml automatically
   cw-tail --config prod      # Uses prod config from ./config.yml
   cw-tail --config dev       # Uses dev config from ./config.yml
   cw-tail --config staging   # Uses staging config from ./config.yml
   ```

3. **Personal overrides (optional):**
   ```bash
   # Create a personal config that won't be committed
   cp config.yml .cw-tail.yml
   # Edit .cw-tail.yml with your personal preferences
   # This will take precedence over config.yml
   ```

## Development

### Setting Up Development Environment

```bash
# Install with development dependencies
uv sync --extra dev

# Run tests (if available)
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .
```

### Making Changes

After making changes to the code:

```bash
# The tool will automatically use your changes when run with:
uv run cw-tail --help

# To reinstall the global tool with your changes:
uv tool install . --force
```

### Testing

The project includes a comprehensive test suite with 89 tests covering:

- **Utility Functions**: Configuration loading, parsing, time conversion
- **CloudWatchTailer Class**: Core functionality, initialization, filtering, highlighting  
- **Formatters**: JSON formatting and processing
- **Main Function**: Command-line interface and integration tests
- **Project-Specific Config**: Config file priority and merging

**Quick Test Commands:**
```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=cw_tail --cov-report=term-missing

# Run tests in verbose mode
uv run pytest -v

# Run specific test file
uv run pytest tests/test_utils.py -v

# Run tests with custom options
uv run pytest tests/ --maxfail=1 -x
```

The test suite achieves **74% code coverage** and all tests are passing.

### AWS CLI Setup Reminder

- Install AWS CLI: Follow the [installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for your operating system.
- Configure AWS Credentials: Run `aws configure` or manually edit your `~/.aws/credentials` file to ensure that your AWS credentials are correctly set up.

## Contributing

Pull requests, bug reports, and suggestions are welcome. Please follow the standard GitHub flow for contributions.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Set up development environment: `uv sync --extra dev`
4. Make your changes
5. Test your changes: `uv run cw-tail --help`
6. Submit a pull request

## License

This project is licensed under the [Unlicense](LICENSE).
