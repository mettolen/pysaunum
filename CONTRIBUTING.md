# Contributing to pysaunum

Thank you for your interest in contributing to pysaunum! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A Saunum sauna controller for testing (optional but recommended)

### Development Setup

1. **Fork and clone the repository**:

   ```bash
   git clone https://github.com/yourusername/pysaunum.git
   cd pysaunum
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:

   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks** (optional but recommended):

   ```bash
   pip install pre-commit
   pre-commit install
   ```

   This will automatically run linting and formatting checks before each commit.

5. **Verify the setup**:

   ```bash
   pytest
   mypy src/pysaunum
   ruff check src/pysaunum
   ```

## 🔧 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add docstrings to all public methods and classes
- Update type hints as needed

### 3. Add Tests

All new features and bug fixes must include tests:

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=pysaunum --cov-report=term-missing

# Run specific test
pytest tests/test_client.py::test_your_new_test -v
```

**Coverage requirement**: Maintain >95% code coverage.

### 4. Type Checking

Ensure all code passes strict type checking:

```bash
mypy src/pysaunum
```

Fix any type errors before submitting your PR.

### 5. Linting

Run ruff to check code style:

```bash
# Check for issues
ruff check src/pysaunum tests/

# Auto-fix issues
ruff check --fix src/pysaunum tests/
```

### 6. Format Code

Code is automatically formatted with ruff:

```bash
ruff format src/pysaunum tests/
```

### 7. Run Pre-commit Checks (Optional)

If you installed pre-commit hooks, they'll run automatically. You can also run them manually:

```bash
pre-commit run --all-files
```

### 8. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add support for fan speed control

- Implement async_set_fan_speed method
- Add fan speed validation
- Update tests and documentation"
```

**Commit message guidelines**:

- Use present tense ("Add feature" not "Added feature")
- First line is a brief summary (50 chars or less)
- Add detailed description after a blank line if needed
- Reference issue numbers when applicable

### 9. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📋 Code Style Guidelines

### Python Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 88 characters (ruff default)
- Use docstrings for all public classes, methods, and functions

### Docstring Format

Use Google-style docstrings:

```python
async def async_set_target_temperature(self, temperature: int) -> None:
    """Set the target temperature.

    Args:
        temperature: Target temperature in Celsius.
            - 0: Use sauna type's default temperature
            - 40-100: Specific temperature in °C

    Raises:
        ValueError: If temperature is out of range
        SaunumConnectionError: If not connected
        SaunumCommunicationError: If write operation fails

    Example:
        >>> await client.async_set_target_temperature(80)
    """
```

### Type Hints

All functions must have complete type hints:

```python
async def async_get_data(self) -> SaunumData:
    """Fetch current data from the sauna controller."""

def convert_value(value: int | None) -> float | None:
    """Convert value handling None case."""
```

### Error Handling

- Use specific exception types from `pysaunum.exceptions`
- Always include error context in exception messages
- Chain exceptions using `raise ... from err`

```python
try:
    result = await self._client.read_holding_registers(...)
except ModbusException as err:
    raise SaunumCommunicationError(
        f"Failed to read registers: {err}"
    ) from err
```

## 🧪 Testing Guidelines

### Test Structure

Tests are located in `tests/` directory:

```
tests/
├── __init__.py
├── test_client.py
├── test_exceptions.py
└── conftest.py  # Shared fixtures
```

### Writing Tests

- Use descriptive test names: `test_connect_raises_error_when_connection_fails`
- Test both success and failure cases
- Mock external dependencies (Modbus communication)
- Use pytest fixtures for common setup

```python
async def test_set_temperature_success(mock_modbus_client):
    """Test successful temperature setting."""
    client = SaunumClient(host="192.168.1.100")
    client._client = mock_modbus_client

    await client.async_set_target_temperature(80)

    mock_modbus_client.write_register.assert_called_once_with(
        address=REG_TARGET_TEMPERATURE,
        value=80,
        device_id=1,
    )

async def test_set_temperature_out_of_range(mock_modbus_client):
    """Test temperature validation."""
    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(200)
```

### Test Coverage

Check coverage after adding tests:

```bash
pytest --cov=pysaunum --cov-report=html
open htmlcov/index.html  # View detailed coverage report
```

## 📖 Documentation

### Update Documentation

When adding features, update:

1. **README.md** - User-facing features
2. **Docstrings** - All public APIs
3. **example.py** - Add usage examples if applicable
4. **CHANGELOG.md** - Document changes (if file exists)

### API Documentation

Public APIs must have comprehensive docstrings:

- Description of what the method does
- All parameters with types and descriptions
- Return value type and description
- All possible exceptions
- Usage examples for complex APIs

## 🐛 Bug Reports

### Before Submitting

- Check existing issues to avoid duplicates
- Test with the latest version
- Gather relevant information:
  - Python version
  - pysaunum version
  - Sauna controller model and firmware version
  - Error messages and stack traces

### Bug Report Template

```markdown
## Description

Brief description of the bug

## Steps to Reproduce

1. Step one
2. Step two
3. ...

## Expected Behavior

What should happen

## Actual Behavior

What actually happens

## Environment

- Python version: 3.13.9
- pysaunum version: 0.1.0
- Sauna controller: Saunum Leil
- OS: Linux/Windows/macOS

## Error Messages
```

Paste error messages and stack traces here

```

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Proposing New Features

1. **Check existing issues** to see if already proposed
2. **Open a discussion** before implementing large features
3. **Describe the use case** - why is this feature needed?
4. **Propose an API** - how should it work?

### Feature Request Template

```markdown
## Feature Description

What feature would you like to see?

## Use Case

Why is this feature needed? What problem does it solve?

## Proposed API

How should the feature work?

## Example usage

await client.async_some_new_feature(param=value)

## Alternatives Considered

What other approaches did you consider?
```

## 🔄 Pull Request Process

### Before Submitting

- [ ] All tests pass: `pytest`
- [ ] Type checking passes: `mypy src/pysaunum`
- [ ] Linting passes: `ruff check src/pysaunum`
- [ ] Code coverage is maintained (>95%)
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Description

Include in your PR:

- **Summary** of changes
- **Motivation** - why is this change needed?
- **Testing** - how was it tested?
- **Breaking changes** - if any
- **Related issues** - link to issues

### Review Process

1. Automated checks will run (tests, linting, type checking)
2. Maintainer will review the code
3. Address any feedback or requested changes
4. Once approved, PR will be merged

### After Your PR is Merged

- Delete your feature branch
- Pull the latest changes from main
- Update your fork

## 🎯 Development Best Practices

### Async/Await

- All I/O operations must be async
- Don't block the event loop
- Use `asyncio.sleep()` not `time.sleep()`

### Error Handling

- Be specific with exception types
- Include helpful error messages
- Don't use bare `except:` clauses

### Performance

- Minimize Modbus read/write operations
- Batch register reads when possible
- Use appropriate timeouts

### Security

- Never log sensitive data (passwords, tokens)
- Validate all user inputs
- Use secure defaults

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue

## 📄 License

By contributing to pysaunum, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## 🙏 Thank You!

Your contributions make pysaunum better for everyone. We appreciate your time and effort!
