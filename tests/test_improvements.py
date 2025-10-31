"""Tests for factory method and strict validation improvements."""

from unittest.mock import AsyncMock, patch

import pytest
from pymodbus.exceptions import ModbusException

from pysaunum import SaunumClient
from pysaunum.exceptions import SaunumConnectionError


class TestFactoryMethod:
    """Test factory method pattern."""

    @pytest.mark.asyncio
    async def test_create_factory_method_success(self) -> None:
        """Test factory method creates and connects client."""
        with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connected = True
            mock_client_class.return_value = mock_client

            # Create client using factory method
            client = await SaunumClient.create("192.168.1.100")

            # Verify client is created and connected
            assert client.host == "192.168.1.100"
            assert client.is_connected
            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_factory_method_connection_failure(self) -> None:
        """Test factory method raises error on connection failure."""
        with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connected = False
            mock_client_class.return_value = mock_client

            # Should raise connection error
            with pytest.raises(SaunumConnectionError, match="Failed to connect"):
                await SaunumClient.create("192.168.1.100")

    @pytest.mark.asyncio
    async def test_create_factory_method_with_custom_params(self) -> None:
        """Test factory method with custom parameters."""
        with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connected = True
            mock_client_class.return_value = mock_client

            # Create with custom params
            client = await SaunumClient.create(
                host="192.168.1.50",
                port=5020,
                device_id=2,
                timeout=5,
            )

            # Verify custom params are used
            assert client.host == "192.168.1.50"
            mock_client_class.assert_called_once_with(
                host="192.168.1.50",
                port=5020,
                timeout=5,
            )

    @pytest.mark.asyncio
    async def test_create_factory_method_oserror(self) -> None:
        """Test factory method handles OSError."""
        with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.side_effect = OSError("Network unreachable")
            mock_client_class.return_value = mock_client

            with pytest.raises(SaunumConnectionError, match="Failed to connect"):
                await SaunumClient.create("192.168.1.100")

    @pytest.mark.asyncio
    async def test_create_factory_method_modbus_exception(self) -> None:
        """Test factory method handles ModbusException."""
        with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.connect.side_effect = ModbusException("Modbus error")
            mock_client_class.return_value = mock_client

            with pytest.raises(SaunumConnectionError, match="Failed to connect"):
                await SaunumClient.create("192.168.1.100")
