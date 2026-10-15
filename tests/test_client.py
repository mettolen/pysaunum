"""Tests for SaunumClient."""
# pylint: disable=redefined-outer-name

from unittest.mock import MagicMock, patch

import pytest
from pymodbus.exceptions import ModbusException

from pysaunum import (
    AutoLeilMode,
    ControllerState,
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


@pytest.mark.usefixtures("mock_modbus_client")
def test_client_init() -> None:
    """Test client initialization."""
    client = SaunumClient(host="192.168.1.100")
    assert client.host == "192.168.1.100"
    assert client.port == 502
    assert client.device_id == 1
    assert not client.is_connected


@pytest.mark.usefixtures("mock_modbus_client")
def test_client_init_empty_host() -> None:
    """Test client initialization with empty host raises ValueError."""
    with pytest.raises(ValueError, match="Host must be a non-empty string"):
        SaunumClient(host="")


@pytest.mark.usefixtures("mock_modbus_client")
def test_client_init_blank_host() -> None:
    """Test client initialization with blank host raises ValueError."""
    with pytest.raises(ValueError, match="Host must be a non-empty string"):
        SaunumClient(host="   ")


@pytest.mark.usefixtures("mock_modbus_client")
def test_client_init_custom_params() -> None:
    """Test client initialization with custom parameters."""
    client = SaunumClient(host="10.0.0.1", port=5020, device_id=3, timeout=5)
    assert client.host == "10.0.0.1"
    assert client.port == 5020
    assert client.device_id == 3


@pytest.mark.usefixtures("mock_modbus_client")
def test_client_repr() -> None:
    """Test client string representation."""
    client = SaunumClient(host="192.168.1.100")
    assert repr(client) == "SaunumClient(192.168.1.100:502, connected=False)"


async def test_connect_success(mock_modbus_client: MagicMock) -> None:
    """Test successful connection."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.connect()

    mock_modbus_client.connect.assert_called_once()
    assert client.is_connected


async def test_connect_failure(mock_modbus_client: MagicMock) -> None:
    """Test connection failure."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError):
        await client.connect()


async def test_get_data_success(mock_modbus_client: MagicMock) -> None:
    """Test successful data retrieval."""
    mock_modbus_client.connected = True

    # Mock control registers response (0-6: session_active, sauna_type, etc.)
    control_response = MagicMock()
    control_response.isError.return_value = False
    # session=1, type=0, duration=60, fan_dur=10, temp=80, fan_speed=2, light=1
    control_response.registers = [1, 0, 60, 10, 80, 2, 1]

    # Mock status registers response (100-109)
    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [75, 1800, 900, 1, 0, 0, 0, 0, 0, 3]

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
    assert data.current_temperature == 75
    assert data.on_time == (1800 << 16) + 900  # Combined 32-bit value
    assert data.heater_elements_active == 1  # 1 heater element active
    assert data.door_open is False
    assert data.controller_state is ControllerState.HEATING
    assert data.session_state is ControllerState.HEATING
    assert data.alarm_door_open is False
    assert data.alarm_door_sensor is False
    assert data.alarm_thermal_cutoff is False
    assert data.alarm_internal_temp is False
    assert data.alarm_temp_sensor_short is False
    assert data.alarm_temp_sensor_open is False


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
    status_response.registers = [65535, 0, 0, 0, 0, 0, 0, 0, 0, 1]

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

    assert data.current_temperature == -1


async def test_get_data_invalid_controller_state(
    mock_modbus_client: MagicMock,
) -> None:
    """Test rejecting an unknown controller state."""
    mock_modbus_client.connected = True

    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [0, 0, 0, 0, 0, 0, 0]

    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [20, 0, 0, 0, 0, 0, 0, 0, 0, 7]

    alarm_response = MagicMock()
    alarm_response.isError.return_value = False
    alarm_response.registers = [0, 0, 0, 0, 0, 0]

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response,
        alarm_response,
    ]

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumInvalidDataError, match="Invalid data received: 7"):
        await client.async_get_data()


async def test_get_data_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test get_data when not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError):
        await client.async_get_data()


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


async def test_set_temperature_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting an invalid temperature."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(150)

    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(30)


async def test_context_manager(mock_modbus_client: MagicMock) -> None:
    """Test using client as async context manager."""
    mock_modbus_client.connected = True

    async with SaunumClient(host="192.168.1.100") as client:
        assert client.is_connected

    mock_modbus_client.connect.assert_called_once()
    mock_modbus_client.close.assert_called_once()


async def test_connect_oserror(mock_modbus_client: MagicMock) -> None:
    """Test connection failure with OSError."""
    mock_modbus_client.connect.side_effect = OSError("Network unreachable")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Network unreachable"):
        await client.connect()


async def test_connect_modbus_exception(mock_modbus_client: MagicMock) -> None:
    """Test connection failure with ModbusException."""
    mock_modbus_client.connect.side_effect = ModbusException("Modbus error")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Modbus error"):
        await client.connect()


async def test_connect_timeout(mock_modbus_client: MagicMock) -> None:
    """Test connection failure with TimeoutError."""
    mock_modbus_client.connect.side_effect = TimeoutError("Connection timed out")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumTimeoutError, match="Timeout connecting"):
        await client.connect()


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
    status_response.registers = [75, 1800, 900, 1, 0, 0, 0, 0, 0, 3]

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


async def test_get_data_timeout_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when timeout occurs."""
    mock_modbus_client.connected = True
    mock_modbus_client.read_holding_registers.side_effect = TimeoutError("Timeout")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumTimeoutError, match="Timeout communicating"):
        await client.async_get_data()


async def test_get_data_modbus_exception(mock_modbus_client: MagicMock) -> None:
    """Test get_data when modbus exception occurs."""
    mock_modbus_client.connected = True
    mock_modbus_client.read_holding_registers.side_effect = ModbusException(
        "Modbus error"
    )

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumCommunicationError, match="Modbus communication error"):
        await client.async_get_data()


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


async def test_get_data_high_target_temperature(
    mock_modbus_client: MagicMock,
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
    status_response.registers = [75, 1800, 900, 1, 0, 0, 0, 0, 0, 3]

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

    # Raw value is passed through even if above the valid 40-100 range
    assert data.target_temperature == 150


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
    status_response.registers = [75, 1800, 900, 1, 0, 0, 0, 0, 0, 3]

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

    # Raw value is passed through even if below the valid 40-100 range
    assert data.target_temperature == 30


async def test_write_register_error(mock_modbus_client: MagicMock) -> None:
    """Test write register with error response."""
    mock_modbus_client.connected = True

    write_response = MagicMock()
    write_response.isError.return_value = True
    mock_modbus_client.write_register.return_value = write_response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumCommunicationError, match="Failed to write register"):
        await client.async_start_session()


async def test_write_register_modbus_exception(mock_modbus_client: MagicMock) -> None:
    """Test write register with modbus exception."""
    mock_modbus_client.connected = True
    mock_modbus_client.write_register.side_effect = ModbusException("Write error")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumCommunicationError, match="Modbus error writing register"):
        await client.async_start_session()


async def test_write_register_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test write register when not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Not connected"):
        await client.async_start_session()


async def test_write_register_timeout(mock_modbus_client: MagicMock) -> None:
    """Test write register when timeout occurs."""
    mock_modbus_client.connected = True
    mock_modbus_client.write_register.side_effect = TimeoutError("Timeout")

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumTimeoutError, match="Timeout writing register"):
        await client.async_start_session()


async def test_set_sauna_duration_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(120)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=120, device_id=1
    )


async def test_set_sauna_duration_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Duration 1081 minutes out of range"):
        await client.async_set_sauna_duration(1081)


async def test_set_sauna_duration_invalid_negative(
    mock_modbus_client: MagicMock,
) -> None:
    """Test setting invalid negative sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Duration -5 minutes out of range"):
        await client.async_set_sauna_duration(-5)


async def test_set_sauna_duration_min_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting minimum valid non-default sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(60)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=60, device_id=1
    )


async def test_set_sauna_duration_below_min_invalid(
    mock_modbus_client: MagicMock,
) -> None:
    """Test rejecting a non-default sauna duration below 60 minutes."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Duration 59 minutes out of range"):
        await client.async_set_sauna_duration(59)


async def test_set_sauna_duration_max_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting maximum valid public sauna duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(1080)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=1080, device_id=1
    )


async def test_set_fan_speed_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid fan speed."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_speed(2)  # Medium speed

    mock_modbus_client.write_register.assert_called_once_with(
        address=5, value=2, device_id=1
    )


async def test_set_fan_speed_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid fan speed."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Fan speed 4 out of range \\(0-3\\)"):
        await client.async_set_fan_speed(4)


async def test_set_sauna_type_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid sauna type 1 (value 0)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(0)  # Type 1 = value 0

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=0, device_id=1
    )


async def test_set_sauna_type_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting a negative sauna preset index."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Sauna type -1 invalid"):
        await client.async_set_sauna_type(-1)


async def test_set_sauna_type_2_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting sauna type 2 (value 1)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(1)  # Type 2 = value 1

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=1, device_id=1
    )


async def test_set_sauna_type_3_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting sauna type 3 (value 2)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(2)  # Type 3 = value 2

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=2, device_id=1
    )


async def test_set_device_dependent_sauna_type_valid(
    mock_modbus_client: MagicMock,
) -> None:
    """Test setting a preset index beyond the convenience enum."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_type(3)

    mock_modbus_client.write_register.assert_called_once_with(
        address=1, value=3, device_id=1
    )


async def test_set_light_control(mock_modbus_client: MagicMock) -> None:
    """Test setting light control."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_light_control(True)

    mock_modbus_client.write_register.assert_called_once_with(
        address=6, value=1, device_id=1
    )


@pytest.mark.parametrize(
    ("method_name", "address", "value"),
    [
        pytest.param("async_restart_software", 7, 0xA55A, id="software-restart"),
        pytest.param("async_close_cooldown", 8, 1, id="close-cooldown"),
        pytest.param("async_dismiss_notifications", 9, 1, id="dismiss-notifications"),
    ],
)
async def test_action_register(
    mock_modbus_client: MagicMock,
    method_name: str,
    address: int,
    value: int,
) -> None:
    """Test sending a one-shot action command."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await getattr(client, method_name)()

    mock_modbus_client.write_register.assert_called_once_with(
        address=address, value=value, device_id=1
    )


@pytest.mark.parametrize(
    ("method_name", "argument", "address", "value"),
    [
        pytest.param(
            "async_set_autoleil_mode",
            AutoLeilMode.INTERVAL,
            10,
            1,
            id="mode",
        ),
        pytest.param("async_set_autoleil_interval", 25, 12, 25, id="interval"),
        pytest.param("async_set_autoleil_water_amount", 40, 13, 40, id="water"),
        pytest.param("async_set_autoleil_ready_mode", True, 15, 1, id="ready-on"),
        pytest.param("async_set_autoleil_ready_mode", False, 15, 0, id="ready-off"),
        pytest.param(
            "async_set_autoleil_auto_ventilation",
            True,
            16,
            1,
            id="ventilation-on",
        ),
        pytest.param(
            "async_set_autoleil_auto_ventilation",
            False,
            16,
            0,
            id="ventilation-off",
        ),
        pytest.param("async_set_autoleil_button_use", True, 17, 1, id="button-use-on"),
        pytest.param(
            "async_set_autoleil_button_use", False, 17, 0, id="button-use-off"
        ),
        pytest.param(
            "async_set_autoleil_button_timeout", 300, 18, 300, id="button-timeout"
        ),
    ],
)
async def test_set_autoleil_value(
    mock_modbus_client: MagicMock,
    method_name: str,
    argument: int | bool,
    address: int,
    value: int,
) -> None:
    """Test setting fixed-range AutoLeil values."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await getattr(client, method_name)(argument)

    mock_modbus_client.write_register.assert_called_once_with(
        address=address, value=value, device_id=1
    )


@pytest.mark.parametrize(
    ("method_name", "argument", "message"),
    [
        pytest.param(
            "async_set_autoleil_mode",
            2,
            "AutoLeil mode 2 out of range",
            id="mode",
        ),
        pytest.param(
            "async_set_autoleil_interval",
            0,
            "AutoLeil interval 0 minutes out of range",
            id="interval-low",
        ),
        pytest.param(
            "async_set_autoleil_interval",
            26,
            "AutoLeil interval 26 minutes out of range",
            id="interval-high",
        ),
        pytest.param(
            "async_set_autoleil_water_amount",
            2,
            "AutoLeil water amount 2 out of range",
            id="water-low",
        ),
        pytest.param(
            "async_set_autoleil_water_amount",
            41,
            "AutoLeil water amount 41 out of range",
            id="water-high",
        ),
        pytest.param(
            "async_set_autoleil_button_timeout",
            10,
            "AutoLeil button timeout 10 seconds invalid",
            id="button-timeout",
        ),
    ],
)
async def test_set_autoleil_value_invalid(
    mock_modbus_client: MagicMock,
    method_name: str,
    argument: int,
    message: str,
) -> None:
    """Test rejecting invalid fixed-range AutoLeil values."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match=message):
        await getattr(client, method_name)(argument)

    mock_modbus_client.write_register.assert_not_called()


async def test_set_autoleil_target_humidity(
    mock_modbus_client: MagicMock,
) -> None:
    """Test setting humidity at the temperature-dependent maximum."""
    mock_modbus_client.connected = True
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [80]
    mock_modbus_client.read_holding_registers.return_value = response

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_autoleil_target_humidity(50)

    mock_modbus_client.read_holding_registers.assert_awaited_once_with(
        address=4, count=1, device_id=1
    )
    mock_modbus_client.write_register.assert_awaited_once_with(
        address=11, value=50, device_id=1
    )


async def test_set_autoleil_target_humidity_negative(
    mock_modbus_client: MagicMock,
) -> None:
    """Test rejecting negative target humidity without reading the controller."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="target humidity cannot be negative"):
        await client.async_set_autoleil_target_humidity(-1)

    mock_modbus_client.read_holding_registers.assert_not_called()


async def test_set_autoleil_target_humidity_above_maximum(
    mock_modbus_client: MagicMock,
) -> None:
    """Test rejecting humidity above the temperature-dependent maximum."""
    mock_modbus_client.connected = True
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [80]
    mock_modbus_client.read_holding_registers.return_value = response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="51% out of range"):
        await client.async_set_autoleil_target_humidity(51)


async def test_set_autoleil_target_humidity_invalid_temperature(
    mock_modbus_client: MagicMock,
) -> None:
    """Test rejecting invalid controller temperature data."""
    mock_modbus_client.connected = True
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [101]
    mock_modbus_client.read_holding_registers.return_value = response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumInvalidDataError, match="Invalid target temperature"):
        await client.async_set_autoleil_target_humidity(20)


@pytest.mark.parametrize(
    ("session_duration", "autoleil_duration"),
    [
        pytest.param(120, 120, id="explicit-session-duration"),
        pytest.param(0, 1080, id="preset-session-duration"),
    ],
)
async def test_set_autoleil_duration(
    mock_modbus_client: MagicMock,
    session_duration: int,
    autoleil_duration: int,
) -> None:
    """Test setting AutoLeil duration against the configured session duration."""
    mock_modbus_client.connected = True
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [session_duration]
    mock_modbus_client.read_holding_registers.return_value = response

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_autoleil_duration(autoleil_duration)

    mock_modbus_client.read_holding_registers.assert_awaited_once_with(
        address=2, count=1, device_id=1
    )
    mock_modbus_client.write_register.assert_awaited_once_with(
        address=14, value=autoleil_duration, device_id=1
    )


@pytest.mark.parametrize(
    ("duration", "message"),
    [
        pytest.param(30, "30 minutes out of range", id="below-minimum"),
        pytest.param(1110, "1110 minutes out of range", id="above-maximum"),
        pytest.param(61, "must use 30-minute steps", id="invalid-step"),
    ],
)
async def test_set_autoleil_duration_invalid(
    mock_modbus_client: MagicMock,
    duration: int,
    message: str,
) -> None:
    """Test rejecting invalid AutoLeil duration ranges and steps."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match=message):
        await client.async_set_autoleil_duration(duration)

    mock_modbus_client.read_holding_registers.assert_not_called()


async def test_set_autoleil_duration_exceeds_session(
    mock_modbus_client: MagicMock,
) -> None:
    """Test rejecting AutoLeil duration above the explicit session duration."""
    mock_modbus_client.connected = True
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [120]
    mock_modbus_client.read_holding_registers.return_value = response

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="150 minutes exceeds session duration 120"):
        await client.async_set_autoleil_duration(150)


async def test_autoleil_dependent_setting_not_connected(
    mock_modbus_client: MagicMock,
) -> None:
    """Test reading dependent settings while disconnected."""
    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(SaunumConnectionError, match="Not connected"):
        await client.async_set_autoleil_target_humidity(20)


@pytest.mark.parametrize(
    ("error", "exception", "message"),
    [
        pytest.param(
            TimeoutError("timeout"),
            SaunumTimeoutError,
            "Timeout reading register 4",
            id="timeout",
        ),
        pytest.param(
            ModbusException("failure"),
            SaunumCommunicationError,
            "Modbus error reading register 4",
            id="modbus-error",
        ),
    ],
)
async def test_autoleil_dependent_setting_read_error(
    mock_modbus_client: MagicMock,
    error: Exception,
    exception: type[Exception],
    message: str,
) -> None:
    """Test errors while reading a dependent controller setting."""
    mock_modbus_client.connected = True
    mock_modbus_client.read_holding_registers.side_effect = error

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(exception, match=message):
        await client.async_set_autoleil_target_humidity(20)


async def test_set_fan_duration_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting valid fan duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_duration(15)

    mock_modbus_client.write_register.assert_called_once_with(
        address=3, value=15, device_id=1
    )


async def test_set_fan_duration_zero(mock_modbus_client: MagicMock) -> None:
    """Test setting fan duration to zero (off)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_duration(0)

    mock_modbus_client.write_register.assert_called_once_with(
        address=3, value=0, device_id=1
    )


async def test_set_fan_duration_max(mock_modbus_client: MagicMock) -> None:
    """Test setting fan duration to maximum (20)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_fan_duration(20)

    mock_modbus_client.write_register.assert_called_once_with(
        address=3, value=20, device_id=1
    )


async def test_set_fan_duration_invalid_high(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid high fan duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Fan duration 21 minutes out of range"):
        await client.async_set_fan_duration(21)


async def test_set_fan_duration_invalid_negative(mock_modbus_client: MagicMock) -> None:
    """Test setting invalid negative fan duration."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Fan duration -1 minutes out of range"):
        await client.async_set_fan_duration(-1)


async def test_set_temperature_zero_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting temperature to zero (off)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_target_temperature(0)

    mock_modbus_client.write_register.assert_called_once_with(
        address=4, value=0, device_id=1
    )


async def test_set_temperature_below_min_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting temperature below minimum (but not zero)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Temperature 39°C out of range"):
        await client.async_set_target_temperature(39)


async def test_set_temperature_negative_invalid(mock_modbus_client: MagicMock) -> None:
    """Test setting negative temperature."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")

    with pytest.raises(ValueError, match="Temperature -1°C out of range"):
        await client.async_set_target_temperature(-1)


async def test_set_sauna_duration_zero_valid(mock_modbus_client: MagicMock) -> None:
    """Test setting sauna duration to zero (off)."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_set_sauna_duration(0)

    mock_modbus_client.write_register.assert_called_once_with(
        address=2, value=0, device_id=1
    )


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

    # Test different heater element counts
    for count in [0, 1, 2, 3]:
        status_response = MagicMock()
        status_response.isError.return_value = False
        # temp=70, on_time_high=0, on_time_low=0, heater_elements=count, door=0
        status_response.registers = [70, 0, 0, count, 0, 0, 0, 0, 0, 3]

        mock_modbus_client.read_holding_registers.side_effect = [
            control_response,
            status_response,
            alarm_response,
        ]

        data = await client.async_get_data()
        assert data.heater_elements_active == count

    # Test heater element count outside typical range - raw value passed through
    status_response_other = MagicMock()
    status_response_other.isError.return_value = False
    status_response_other.registers = [70, 0, 0, 5, 0, 0, 0, 0, 0, 3]

    mock_modbus_client.read_holding_registers.side_effect = [
        control_response,
        status_response_other,
        alarm_response,
    ]

    data = await client.async_get_data()
    assert data.heater_elements_active == 5


async def test_async_close_calls_close(mock_modbus_client: MagicMock) -> None:
    """Ensure async_close calls underlying close."""
    mock_modbus_client.connected = True

    client = SaunumClient(host="192.168.1.100")
    await client.async_close()

    mock_modbus_client.close.assert_called_once()


async def test_get_data_fan_speed_validation(mock_modbus_client: MagicMock) -> None:
    """Test fan speed validation for different values."""
    mock_modbus_client.connected = True

    # Mock status and alarm registers response
    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [70, 0, 0, 1, 0, 0, 0, 0, 0, 3]

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


async def test_get_data_invalid_data_error(mock_modbus_client: MagicMock) -> None:
    """Test get_data when invalid data structure causes parsing error."""
    mock_modbus_client.connected = True

    # Mock valid response structure but cause ValueError in SaunumData creation
    control_response = MagicMock()
    control_response.isError.return_value = False
    control_response.registers = [1, 1, 60, 0, 80, 3, 1]

    status_response = MagicMock()
    status_response.isError.return_value = False
    status_response.registers = [75, 0, 100, 3, 0, 0, 0, 0, 0, 3]

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


async def test_async_close_when_not_connected(mock_modbus_client: MagicMock) -> None:
    """Test async_close when client is not connected."""
    mock_modbus_client.connected = False

    client = SaunumClient(host="192.168.1.100")
    await client.async_close()

    # close should not be called when not connected
    mock_modbus_client.close.assert_not_called()


async def test_create_factory_method_success(mock_modbus_client: MagicMock) -> None:
    """Test factory method creates and connects client."""
    mock_modbus_client.connected = True

    client = await SaunumClient.create("192.168.1.100")

    assert client.host == "192.168.1.100"
    assert client.is_connected
    mock_modbus_client.connect.assert_called_once()


async def test_create_factory_method_connection_failure(
    mock_modbus_client: MagicMock,
) -> None:
    """Test factory method raises error on connection failure."""
    mock_modbus_client.connected = False

    with pytest.raises(SaunumConnectionError, match="Failed to connect"):
        await SaunumClient.create("192.168.1.100")


async def test_create_factory_method_with_custom_params(
    mock_modbus_client: MagicMock,
) -> None:
    """Test factory method with custom parameters."""
    mock_modbus_client.connected = True

    client = await SaunumClient.create(
        host="192.168.1.50",
        port=5020,
        device_id=2,
        timeout=5,
    )

    assert client.host == "192.168.1.50"


async def test_create_factory_method_oserror(mock_modbus_client: MagicMock) -> None:
    """Test factory method handles OSError."""
    mock_modbus_client.connect.side_effect = OSError("Network unreachable")

    with pytest.raises(SaunumConnectionError, match="Failed to connect"):
        await SaunumClient.create("192.168.1.100")


async def test_create_factory_method_modbus_exception(
    mock_modbus_client: MagicMock,
) -> None:
    """Test factory method handles ModbusException."""
    mock_modbus_client.connect.side_effect = ModbusException("Modbus error")

    with pytest.raises(SaunumConnectionError, match="Failed to connect"):
        await SaunumClient.create("192.168.1.100")
