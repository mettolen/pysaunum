"""Saunum sauna controller client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    MAX_TEMPERATURE,
    MIN_TEMPERATURE,
    REG_CURRENT_TEMP,
    REG_HEATER_STATUS_OFFSET,
    REG_SESSION_ACTIVE,
    REG_TARGET_TEMPERATURE,
    WRITE_SETTLE_SECONDS,
)
from .exceptions import (
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumInvalidDataError,
    SaunumTimeoutError,
)
from .models import SaunumData

_LOGGER = logging.getLogger(__name__)


class SaunumClient:
    """Client for Saunum sauna controller."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        device_id: int = DEFAULT_DEVICE_ID,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Saunum client.

        Args:
            host: IP address or hostname of the sauna controller
            port: Modbus TCP port (default: 502)
            device_id: Modbus device/unit ID (default: 1)
            timeout: Connection timeout in seconds (default: 10)
        """
        self._host = host
        self._port = port
        self._device_id = device_id
        self._timeout = timeout
        self._client = AsyncModbusTcpClient(
            host=host,
            port=port,
            timeout=timeout,
        )

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected."""
        return self._client.connected

    async def connect(self) -> None:
        """Connect to the sauna controller.

        Raises:
            SaunumConnectionError: If connection fails
        """
        try:
            await self._client.connect()
            if not self._client.connected:
                raise SaunumConnectionError(
                    f"Failed to connect to {self._host}:{self._port}"
                )
        except (OSError, ModbusException) as err:
            raise SaunumConnectionError(
                f"Failed to connect to {self._host}:{self._port}: {err}"
            ) from err

    async def close(self) -> None:
        """Close the connection to the sauna controller."""
        if self._client.connected:
            self._client.close()

    async def async_get_data(self) -> SaunumData:
        """Fetch current data from the sauna controller.

        Returns:
            SaunumData object with current state

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If communication fails
            SaunumTimeoutError: If request times out
            SaunumInvalidDataError: If response data is invalid
        """
        if not self._client.connected:
            raise SaunumConnectionError("Not connected to sauna controller")

        try:
            # Read essential registers for session control
            holding_result = await self._client.read_holding_registers(
                address=REG_SESSION_ACTIVE,
                count=5,
                device_id=self._device_id,
            )
            if holding_result.isError():
                raise SaunumCommunicationError(
                    f"Failed to read holding registers: {holding_result}"
                )

            # Read temperature sensor and heater status
            sensor_result = await self._client.read_holding_registers(
                address=REG_CURRENT_TEMP,
                count=4,
                device_id=self._device_id,
            )
            if sensor_result.isError():
                raise SaunumCommunicationError(
                    f"Failed to read sensor registers: {sensor_result}"
                )

            holding_regs = holding_result.registers
            sensor_regs = sensor_result.registers

            # Parse data
            session_active = bool(holding_regs[0])
            target_temp_raw = holding_regs[4]
            current_temp_raw = sensor_regs[0]
            heater_status = bool(sensor_regs[REG_HEATER_STATUS_OFFSET])

            # Validate target temperature
            target_temp: int | None = None
            if target_temp_raw >= MIN_TEMPERATURE:
                if target_temp_raw > MAX_TEMPERATURE:
                    _LOGGER.warning(
                        "Target temperature %d°C exceeds maximum %d°C",
                        target_temp_raw,
                        MAX_TEMPERATURE,
                    )
                target_temp = target_temp_raw

            # Current temperature can be any value
            current_temp: float | None = float(current_temp_raw)

            return SaunumData(
                session_active=session_active,
                target_temperature=target_temp,
                current_temperature=current_temp,
                heater_on=heater_status,
            )

        except TimeoutError as err:
            raise SaunumTimeoutError(
                f"Timeout communicating with {self._host}:{self._port}"
            ) from err
        except ModbusException as err:
            raise SaunumCommunicationError(
                f"Modbus communication error: {err}"
            ) from err
        except (IndexError, KeyError, ValueError) as err:
            raise SaunumInvalidDataError(f"Invalid data received: {err}") from err

    async def async_start_session(self) -> None:
        """Start a sauna session.

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        await self._async_write_register(REG_SESSION_ACTIVE, 1)

    async def async_stop_session(self) -> None:
        """Stop the sauna session.

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        await self._async_write_register(REG_SESSION_ACTIVE, 0)

    async def async_set_target_temperature(self, temperature: int) -> None:
        """Set the target temperature.

        Args:
            temperature: Target temperature in Celsius (40-100)

        Raises:
            ValueError: If temperature is out of range
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        if not MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE:
            raise ValueError(
                f"Temperature {temperature}°C out of range "
                f"({MIN_TEMPERATURE}-{MAX_TEMPERATURE}°C)"
            )

        await self._async_write_register(REG_TARGET_TEMPERATURE, temperature)

    async def _async_write_register(self, address: int, value: int) -> None:
        """Write a single holding register.

        Args:
            address: Register address
            value: Value to write

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        if not self._client.connected:
            raise SaunumConnectionError("Not connected to sauna controller")

        try:
            result = await self._client.write_register(
                address=address,
                value=value,
                device_id=self._device_id,
            )
            if result.isError():
                raise SaunumCommunicationError(
                    f"Failed to write register {address}: {result}"
                )

            # Give the device time to process the write
            await asyncio.sleep(WRITE_SETTLE_SECONDS)

        except ModbusException as err:
            raise SaunumCommunicationError(
                f"Modbus error writing register {address}: {err}"
            ) from err

    async def __aenter__(self) -> SaunumClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
