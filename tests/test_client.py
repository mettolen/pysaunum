"""Tests for SaunumClient."""
# pylint: disable=redefined-outer-name

import asyncio
import threading
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymodbus.exceptions import ModbusException

from pysaunum import (
    SaunumClient,
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumData,
    SaunumInvalidDataError,
    SaunumTimeoutError,
)
from pysaunum.const import (
    DEFAULT_DEVICE_ID,
    REG_SESSION_ACTIVE,
    REG_TARGET_TEMPERATURE,
)


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


@pytest.mark.asyncio
async def test_client_init() -> None:
    """Test client initialization."""
    client = SaunumClient(host="192.168.1.100")
    assert client.host == "192.168.1.100"
    assert not client.is_connected


@pytest.mark.asyncio
async def test_connect_success(mock_modbus_client: MagicMock) -> None:
    """Test successful connection."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.connect()

    mock_modbus_client.connect.assert_called_once()
    assert client.is_connected


@pytest.mark.asyncio
async def test_connect_failure(mock_modbus_client: MagicMock) -> None:
    """Test connection failure."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError):
        await client.connect()


@pytest.mark.asyncio
async def test_get_data_success(mock_modbus_client: MagicMock) -> None:
    """Test successful data retrieval."""
    mock_modbus_client.connected = True

    # Mock control registers response (0-6: session_active, sauna_type, etc.)
    control_response = MagicMock()
    control_response.isError.return_value = False
    # session=1, type=0, duration=60, fan_dur=10, temp=80, fan_speed=2, light=1
    control_response.registers = [1, 0, 60, 10, 80, 2, 1]

    # Mock status registers response (100-104: current_temp, on_time, heater, door)
    status_response = MagicMock()
    status_response.isError.return_value = False
    # temp=75, on_time_high=1800, on_time_low=900, heater=1, door=0
    status_response.registers = [75, 1800, 900, 1, 0]

    # Mock alarm registers response (200-205: all alarm states)
    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]  # all alarms off

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")
    data = await client.async_get_data()

    assert isinstance(data, SaunumData)
    assert data.session_active is True
    assert data.sauna_type == 0
    assert data.sauna_duration == 60
    assert data.fan_duration == 10
    assert data.target_temperature == 80
    assert data.fan_speed == 2  # Medium speed
    assert data.light_on is True
    assert data.current_temperature == 75.0
    assert data.on_time == (1800 << 16) + 900  # Combined 32-bit value
    assert data.heater_elements_active == 1  # 1 heater element active
    assert data.door_open is False
    assert data.alarm_door_open is False
    assert data.alarm_door_sensor is False
    assert data.alarm_thermal_cutoff is False
    assert data.alarm_internal_temp is False
    assert data.alarm_temp_sensor_short is False
    assert data.alarm_temp_sensor_open is False


@pytest.mark.asyncio
async def test_get_data_negative_current_temperature(
    mock_modbus_client: MagicMock,
) -> None:
    """Test current temperature parsing for negative values.

    Saunum encodes negative temperatures as signed 16-bit integers. When read as an
    unsigned Modbus register, -1°C is represented as 65535 (0xFFFF).
    """
    mock_modbus_client.connected = True

    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [0, 0, 0, 0, 0, 0, 0]

    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [65535, 0, 0, 0, 0]

    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")
    data = await client.async_get_data()

    assert data.current_temperature == -1.0


@pytest.mark.asyncio
async def test_get_data_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test get_data when not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_start_session(mock_modbus_client: MagicMock) -> None:
    """Test starting a session."""
    mock_modbus_client.connected = True

    write_response = MagicMock()
    write_response.isError.return_value = False
    mock_modbus_client.write_register.return_value = write_response

    client = SaunumClient(host="192.168.1.100")
    await client.async_start_session()

    mock_modbus_client.write_register.assert_called_once_with(
        address=REG_SESSION_ACTIVE,
        value=1,
        device_id=DEFAULT_DEVICE_ID,
    )


@pytest.mark.asyncio
async def test_stop_session(mock_modbus_client: MagicMock) -> None:
    """Test stopping a session."""
    mock_modbus_client.connected = True

    write_response = MagicMock()
    write_response.isError.return_value = False
    mock_modbus_client.write_register.return_value = write_response

    client = SaunumClient(host="192.168.1.100")
    await client.async_stop_session()

    mock_modbus_client.write_register.assert_called_once_with(
        address=REG_SESSION_ACTIVE,
        value=0,
        device_id=DEFAULT_DEVICE_ID,
    )


@pytest.mark.asyncio
async def test_set_temperature_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting a valid temperature."""
    mock_modbus_client.connected = True

    write_response = MagicMock()
    write_response.isError.return_value = False
    mock_modbus_client.write_register.return_value = write_response

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_target_temperature(80)

    mock_modbus_client.write_register.assert_called_once_with(
        address=REG_TARGET_TEMPERATURE,
        value=80,
        device_id=DEFAULT_DEVICE_ID,
    )


@pytest.mark.asyncio
async def test_set_temperature_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting an invalid temperature."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(150)

    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(30)


@pytest.mark.asyncio
async def test_context_manager(mock_modbus_client: MagicMock) -> None:
    """Test using client as async context manager."""
    mock_modbus_client.connected = True

    async with SaunumClient(host="192.168.1.100") as client:
        assert client.is_connected

    mock_modbus_client.connect.assert_called_once()
    mock_modbus_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_connect_oserror(mock_modbus_client: MagicMock) -> None:
    """Test connection failure with OSError."""
    mock_modbus_client.connect.side_effect = OSError("Network unreachable")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Network unreachable"):
        await client.connect()


@pytest.mark.asyncio
async def test_connect_modbus_exception(mock_modbus_client: MagicMock) -> None:
    """Test connection failure with ModbusException."""
    mock_modbus_client.connect.side_effect = ModbusException("Modbus error")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Modbus error"):
        await client.connect()


@pytest.mark.asyncio
async def test_close_when_connected(mock_modbus_client: MagicMock) -> None:
    """Test closing connection when connected."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    client.close()

    mock_modbus_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_when_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test closing connection when not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")
    client.close()

    mock_modbus_client.close.assert_not_called()


@pytest.mark.asyncio
async def test_get_data_holding_registers_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when holding registers read fails."""
    mock_modbus_client.connected = True

    # Mock holding registers response with error
    holding_response = MagicMock()
    holding_response.isError.return_value = True
    mock_modbus_client.read_holding_registers.return_value = holding_response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(
        SaunumCommunicationError, match="Failed to read control registers"
    ):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_get_data_sensor_registers_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when status registers read fails."""
    mock_modbus_client.connected = True

    # Mock successful control registers response
    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [1, 0, 60, 10, 80, 2, 1]

    # Mock status registers response with error
    status_response = MagicMock()
    status_response.isError.return_value = True

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
    ]

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(
        SaunumCommunicationError, match="Failed to read status registers"
    ):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_get_data_alarm_registers_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when alarm registers read fails."""
    mock_modbus_client.connected = True

    # Mock successful control registers response
    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [1, 0, 60, 10, 80, 2, 1]

    # Mock successful status registers response
    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [75, 1800, 900, 1, 0]

    # Mock alarm registers response with error
    alarm_response = MagicMock()
    alarm_response.isError.return_value = True

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(
        SaunumCommunicationError, match="Failed to read alarm registers"
    ):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_get_data_timeout_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when timeout occurs."""
    mock_modbus_client.connected = True
    mock_modbus_client.read_holding_registers.side_effect = TimeoutError("Timeout")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumTimeoutError, match="Timeout communicating"):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_get_data_modbus_exception(mock_modbus_client: MagicMock) -> None:
    """Test get_data when modbus exception occurs."""
    mock_modbus_client.connected = True
    mock_modbus_client.read_holding_registers.side_effect = ModbusException(
        "Modbus error"
    )

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumCommunicationError, match="Modbus communication error"):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_get_data_invalid_data(mock_modbus_client: MagicMock) -> None:
    """Test get_data when invalid data is received."""
    mock_modbus_client.connected = True

    # Mock holding registers response with insufficient data
    holding_response = MagicMock()
    holding_response.isError.return_value = False
    holding_response.registers = [1]  # Not enough registers

    mock_modbus_client.read_holding_registers.return_value = holding_response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(
        SaunumInvalidDataError, match="Incomplete control register data"
    ):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_get_data_high_target_temperature(
    mock_modbus_client: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test get_data with target temperature above maximum."""
    mock_modbus_client.connected = True

    # Mock control registers response with high temperature
    control_response = MagicMock()
    control_response.isError.return_value = False
    # Target temp = 150°C (above max)
    control_response.registers = [1, 0, 60, 10, 150, 2, 1]

    # Mock status registers response
    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [75, 1800, 900, 1, 0]

    # Mock alarm registers response
    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")
    data = await client.async_get_data()

    # Should log warning and still set the temperature
    assert "exceeds maximum" in caplog.text
    assert data.target_temperature == 150


@pytest.mark.asyncio
async def test_get_data_low_target_temperature(mock_modbus_client: MagicMock) -> None:
    """Test get_data with target temperature below minimum."""
    mock_modbus_client.connected = True

    # Mock control registers response with low temperature
    control_response = MagicMock()
    control_response.isError.return_value = False
    # Target temp = 30°C (below min)
    control_response.registers = [1, 0, 60, 10, 30, 2, 1]

    # Mock status registers response
    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [75, 1800, 900, 1, 0]

    # Mock alarm registers response
    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")
    data = await client.async_get_data()

    # Should not set target temperature for values below minimum
    assert data.target_temperature is None


@pytest.mark.asyncio
async def test_write_register_error(mock_modbus_client: MagicMock) -> None:
    """Test write register with error response."""
    mock_modbus_client.connected = True

    write_response = MagicMock()
    write_response.isError.return_value = True
    mock_modbus_client.write_register.return_value = write_response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumCommunicationError, match="Failed to write register"):
        await client.async_start_session()


@pytest.mark.asyncio
async def test_write_register_modbus_exception(mock_modbus_client: MagicMock) -> None:
    """Test write register with modbus exception."""
    mock_modbus_client.connected = True
    mock_modbus_client.write_register.side_effect = ModbusException("Write error")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumCommunicationError, match="Modbus error writing register"):
        await client.async_start_session()


@pytest.mark.asyncio
async def test_write_register_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test write register when not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Not connected"):
        await client.async_start_session()


@pytest.mark.asyncio
async def test_write_register_timeout(mock_modbus_client: MagicMock) -> None:
    """Test write register when timeout occurs."""
    mock_modbus_client.connected = True
    mock_modbus_client.write_register.side_effect = TimeoutError("Timeout")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumTimeoutError, match="Timeout writing register"):
        await client.async_start_session()


@pytest.mark.asyncio
async def test_set_sauna_duration_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(120)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=120, device_id=1
    )


@pytest.mark.asyncio
async def test_set_sauna_duration_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Duration 800 minutes out of range"):
        await client.async_set_sauna_duration(800)


@pytest.mark.asyncio
async def test_set_sauna_duration_invalid_negative(
    mock_modbus_client: MagicMock,
) -> None:
    """Test setting invalid negative sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Duration -5 minutes out of range"):
        await client.async_set_sauna_duration(-5)


@pytest.mark.asyncio
async def test_set_sauna_duration_min_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting minimum valid sauna duration (1 minute)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(1)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=1, device_id=1
    )


@pytest.mark.asyncio
async def test_set_sauna_duration_max_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting maximum valid sauna duration (720 minutes / 12 hours)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(720)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=720, device_id=1
    )


@pytest.mark.asyncio
async def test_set_fan_speed_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid fan speed."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_speed(2)  # Medium speed

    mock_modbus_client.write_register.assert_called_once_with(
        address=5, value=2, device_id=1
    )


@pytest.mark.asyncio
async def test_set_fan_speed_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid fan speed."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Fan speed 4 out of range \\(0-3\\)"):
        await client.async_set_fan_speed(4)


@pytest.mark.asyncio
async def test_set_sauna_type_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid sauna type 1 (value 0)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(0)  # Type 1 = value 0

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=0, device_id=1
    )


@pytest.mark.asyncio
async def test_set_sauna_type_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid sauna type."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Sauna type 3 invalid"):
        await client.async_set_sauna_type(3)


@pytest.mark.asyncio
async def test_set_sauna_type_2_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting sauna type 2 (value 1)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(1)  # Type 2 = value 1

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=1, device_id=1
    )


@pytest.mark.asyncio
async def test_set_sauna_type_3_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting sauna type 3 (value 2)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(2)  # Type 3 = value 2

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=2, device_id=1
    )


@pytest.mark.asyncio
async def test_set_light_control(mock_modbus_client: MagicMock) -> None:
    """Test setting light control."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_light_control(True)

    mock_modbus_client.write_register.assert_called_once_with(
        address=6, value=1, device_id=1
    )


@pytest.mark.asyncio
async def test_set_fan_duration_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid fan duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_duration(15)

    mock_modbus_client.write_register.assert_called_once_with(
        address=3, value=15, device_id=1
    )


@pytest.mark.asyncio
async def test_set_fan_duration_zero(mock_modbus_client: MagicMock) -> None:
    """Test setting fan duration to zero (off)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_duration(0)

    mock_modbus_client.write_register.assert_called_once_with(
        address=3, value=0, device_id=1
    )


@pytest.mark.asyncio
async def test_set_fan_duration_max(mock_modbus_client: MagicMock) -> None:
    """Test setting fan duration to maximum (30)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_duration(30)

    mock_modbus_client.write_register.assert_called_once_with(
        address=3, value=30, device_id=1
    )


@pytest.mark.asyncio
async def test_set_fan_duration_invalid_high(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid high fan duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Fan duration 31 minutes out of range"):
        await client.async_set_fan_duration(31)


@pytest.mark.asyncio
async def test_set_fan_duration_invalid_negative(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid negative fan duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Fan duration -1 minutes out of range"):
        await client.async_set_fan_duration(-1)


@pytest.mark.asyncio
async def test_set_temperature_zero_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting temperature to zero (off)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_target_temperature(0)

    mock_modbus_client.write_register.assert_called_once_with(
        address=4, value=0, device_id=1
    )


@pytest.mark.asyncio
async def test_set_temperature_below_min_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting temperature below minimum (but not zero)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Temperature 39°C out of range"):
        await client.async_set_target_temperature(39)


@pytest.mark.asyncio
async def test_set_temperature_negative_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting negative temperature."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Temperature -1°C out of range"):
        await client.async_set_target_temperature(-1)


@pytest.mark.asyncio
async def test_set_sauna_duration_zero_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting sauna duration to zero (off)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(0)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=0, device_id=1
    )


@pytest.mark.asyncio
async def test_get_data_heater_elements_count(mock_modbus_client: MagicMock) -> None:
    """Test heater elements count parsing for different values."""
    mock_modbus_client.connected = True

    # Mock control registers response
    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [0, 1, 0, 0, 0, 0, 0]  # minimal control data

    # Mock alarm registers response
    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]  # all alarms off

    client = SaunumClient(host="192.168.1.100")

    # Test different heater element counts (0-3)
    for count in [0, 1, 2, 3]:
        status_response = MagicMock()
        status_response.isError.return_value = False
        # temp=70, on_time_high=0, on_time_low=0, heater_elements=count, door=0
        status_response.registers = [70, 0, 0, count, 0]

        mock_modbus_client.read_holding_registers.side_effect = [
            control_response,
            status_response,
            alarm_response,
        ]

        data = await client.async_get_data()
        assert data.heater_elements_active == count

    # Test invalid heater element count (>3) - should return None
    status_response_invalid = MagicMock()
    status_response_invalid.isError.return_value = False
    status_response_invalid.registers = [70, 0, 0, 5, 0]  # invalid count

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response_invalid,
        alarm_response,
    ]

    data = await client.async_get_data()
    assert data.heater_elements_active is None


@pytest.mark.asyncio
async def test_async_close_awaits_coroutine(mock_modbus_client: MagicMock) -> None:
    """Ensure async_close awaits coroutine close implementations."""
    mock_modbus_client.connected = True
    close_mock = AsyncMock()
    mock_modbus_client.close = close_mock

    client = SaunumClient(host="192.168.1.100")
    await client.async_close()

    close_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_data_fan_speed_validation(mock_modbus_client: MagicMock) -> None:
    """Test fan speed validation for different values."""
    mock_modbus_client.connected = True

    # Mock status and alarm registers response
    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [70, 0, 0, 1, 0]  # standard status data

    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]  # all alarms off

    client = SaunumClient(host="192.168.1.100")

    # Test valid fan speeds (0-3)
    for speed in [0, 1, 2, 3]:
        control_response = MagicMock()
        control_response.isError.return_value = False
        # session=1, type=1, duration=0, fan_dur=0, temp=0, fan_speed=speed, light=0
        control_response.registers = [1, 1, 0, 0, 0, speed, 0]

        mock_modbus_client.read_holding_registers.side_effect = [
            control_response,
            status_response,
            alarm_response,
        ]

        data = await client.async_get_data()
        assert data.fan_speed == speed

    # Test invalid fan speed (>3) - should return None
    control_response_invalid = MagicMock()
    control_response_invalid.isError.return_value = False
    control_response_invalid.registers = [1, 1, 0, 0, 0, 5, 0]  # invalid speed

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response_invalid,
        status_response,
        alarm_response,
    ]

    data = await client.async_get_data()
    assert data.fan_speed is None

    # Test negative fan speed - should return None
    control_response_negative = MagicMock()
    control_response_negative.isError.return_value = False
    control_response_negative.registers = [1, 1, 0, 0, 0, -1, 0]  # negative speed

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response_negative,
        status_response,
        alarm_response,
    ]

    data = await client.async_get_data()
    assert data.fan_speed is None


@pytest.mark.asyncio
async def test_get_data_invalid_data_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when invalid data structure causes parsing error."""
    mock_modbus_client.connected = True

    # Mock valid response structure but cause ValueError in SaunumData creation
    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [1, 1, 60, 0, 80, 3, 1]

    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [75, 0, 100, 3, 0]

    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")

    # Mock SaunumData to raise a ValueError
    with patch("pysaunum.client.SaunumData") as mock_data:
        mock_data.side_effect = ValueError("Test error")
        with pytest.raises(SaunumInvalidDataError, match="Invalid data received"):
            await client.async_get_data()


@pytest.mark.asyncio
async def test_async_close_when_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test async_close when client is not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")
    await client.async_close()

    # close should not be called when not connected
    mock_modbus_client.close.assert_not_called()


@pytest.mark.asyncio
async def test_close_with_coroutine_function(mock_modbus_client: MagicMock) -> None:
    """Test close when client.close is a coroutine function."""
    mock_modbus_client.connected = True

    async def async_close_method():
        """Mock async close method."""

    mock_modbus_client.close = async_close_method

    client = SaunumClient(host="192.168.1.100")
    client.close()

    # Give the event loop time to process the task
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_close_with_coroutine_no_running_loop(
    mock_modbus_client: MagicMock,
) -> None:
    """Test close when client.close is a coroutine function and no loop is running."""
    mock_modbus_client.connected = True

    async def async_close_method():
        """Mock async close method."""

    mock_modbus_client.close = async_close_method

    client = SaunumClient(host="192.168.1.100")

    # Run in a separate thread without event loop

    def run_close():
        """Run close in thread without event loop."""
        client.close()

    thread = threading.Thread(target=run_close)
    thread.start()
    thread.join(timeout=1.0)
