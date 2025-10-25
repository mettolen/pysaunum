"""Tests for SaunumClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pysaunum import (
    SaunumClient,
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumData,
)
from pysaunum.const import (
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    REG_CURRENT_TEMP,
    REG_SESSION_ACTIVE,
    REG_TARGET_TEMPERATURE,
)


@pytest.fixture
def mock_modbus_client():
    """Create a mocked Modbus client."""
    with patch("pysaunum.client.AsyncModbusTcpClient") as mock:
        client = MagicMock()
        client.connected = False
        client.connect = AsyncMock()
        client.close = MagicMock()
        client.read_holding_registers = AsyncMock()
        client.write_register = AsyncMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_client_init():
    """Test client initialization."""
    client = SaunumClient(host="192.168.1.100")
    assert client.host == "192.168.1.100"
    assert not client.is_connected


@pytest.mark.asyncio
async def test_connect_success(mock_modbus_client):
    """Test successful connection."""
    mock_modbus_client.connected = True
    
    client = SaunumClient(host="192.168.1.100")
    await client.connect()
    
    mock_modbus_client.connect.assert_called_once()
    assert client.is_connected


@pytest.mark.asyncio
async def test_connect_failure(mock_modbus_client):
    """Test connection failure."""
    mock_modbus_client.connected = False
    
    client = SaunumClient(host="192.168.1.100")
    
    with pytest.raises(SaunumConnectionError):
        await client.connect()


@pytest.mark.asyncio
async def test_get_data_success(mock_modbus_client):
    """Test successful data retrieval."""
    mock_modbus_client.connected = True
    
    # Mock holding registers response (session_active + target_temp)
    holding_response = MagicMock()
    holding_response.isError.return_value = False
    holding_response.registers = [1, 0, 0, 0, 80]  # session active, target=80
    
    # Mock sensor registers response (current_temp + heater_status)
    sensor_response = MagicMock()
    sensor_response.isError.return_value = False
    sensor_response.registers = [75, 0, 0, 1]  # current=75, heater on
    
    mock_modbus_client.read_holding_registers.side_effect = [
        holding_response,
        sensor_response,
    ]
    
    client = SaunumClient(host="192.168.1.100")
    data = await client.async_get_data()
    
    assert isinstance(data, SaunumData)
    assert data.session_active is True
    assert data.target_temperature == 80
    assert data.current_temperature == 75.0
    assert data.heater_on is True


@pytest.mark.asyncio
async def test_get_data_not_connected(mock_modbus_client):
    """Test get_data when not connected."""
    mock_modbus_client.connected = False
    
    client = SaunumClient(host="192.168.1.100")
    
    with pytest.raises(SaunumConnectionError):
        await client.async_get_data()


@pytest.mark.asyncio
async def test_start_session(mock_modbus_client):
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
async def test_stop_session(mock_modbus_client):
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
async def test_set_temperature_valid(mock_modbus_client):
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
async def test_set_temperature_invalid(mock_modbus_client):
    """Test setting an invalid temperature."""
    mock_modbus_client.connected = True
    
    client = SaunumClient(host="192.168.1.100")
    
    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(150)
    
    with pytest.raises(ValueError, match="out of range"):
        await client.async_set_target_temperature(30)


@pytest.mark.asyncio
async def test_context_manager(mock_modbus_client):
    """Test using client as async context manager."""
    mock_modbus_client.connected = True
    
    async with SaunumClient(host="192.168.1.100") as client:
        assert client.is_connected
    
    mock_modbus_client.connect.assert_called_once()
    mock_modbus_client.close.assert_called_once()
