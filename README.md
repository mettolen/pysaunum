# pysaunum

Python library for controlling Saunum sauna controllers via Modbus TCP.

## Features

- Async/await support using asyncio
- Read current temperature and heater status
- Control sauna sessions (start/stop)
- Set target temperature
- Type hints for better IDE support

## Installation

```bash
pip install pysaunum
```

## Usage

```python
import asyncio
from pysaunum import SaunumClient

async def main():
    # Create client
    client = SaunumClient(host="192.168.1.100", port=502, device_id=1)
    
    try:
        # Connect to the sauna controller
        await client.connect()
        
        # Read current state
        data = await client.async_get_data()
        print(f"Current temperature: {data.current_temperature}°C")
        print(f"Target temperature: {data.target_temperature}°C")
        print(f"Session active: {data.session_active}")
        print(f"Heater on: {data.heater_on}")
        
        # Start a sauna session
        await client.async_start_session()
        
        # Set target temperature to 80°C
        await client.async_set_target_temperature(80)
        
        # Stop the session
        await client.async_stop_session()
        
    finally:
        # Always close the connection
        await client.close()

asyncio.run(main())
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/pysaunum.git
cd pysaunum

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy src/pysaunum

# Run linting
ruff check src/pysaunum
```

## License

MIT License - see LICENSE file for details.

## Credits

This library is designed to work with Saunum sauna controllers and is used by the 
[Home Assistant Saunum integration](https://www.home-assistant.io/integrations/saunum/).
