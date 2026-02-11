"""Shared test fixtures for pysaunum tests."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_modbus_client() -> Iterator[MagicMock]:
    """Mock the AsyncModbusTcpClient."""
    with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client:
        # Set up the mock client instance
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Configure the connected property
        mock_instance.connected = False

        # Mock successful connection
        mock_instance.connect = AsyncMock(return_value=None)
        mock_instance.close = MagicMock(return_value=None)

        # Mock successful read operations
        mock_instance.read_holding_registers = AsyncMock()

        # Mock successful write operation
        mock_write_result = MagicMock()
        mock_write_result.isError.return_value = False
        mock_instance.write_register = AsyncMock(return_value=mock_write_result)

        yield mock_instance


@pytest.fixture
def mock_register_responses() -> dict[str, MagicMock]:
    """Create standard mock register responses for data retrieval tests.

    Returns a dict with 'control', 'status', and 'alarm' mock responses
    using typical default values.
    """
    control_response = MagicMock()
    control_response.isError.return_value = False
    # session=1, type=0, duration=60, fan_dur=10, temp=80, fan_speed=2, light=1
    control_response.registers = [1, 0, 60, 10, 80, 2, 1]

    status_response = MagicMock()
    status_response.isError.return_value = False
    # temp=75, on_time_high=0, on_time_low=0, heater=1, door=0
    status_response.registers = [75, 0, 0, 1, 0]

    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]  # all alarms off

    return {
        "control": control_response,
        "status": status_response,
        "alarm": alarm_response,
    }
