"""Saunum sauna controller client."""

from __future__ import annotations

import logging
from typing import Any, Self, cast

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_TEMPERATURE,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_TEMPERATURE,
    REG_ALARM_DOOR_OPEN,
    REG_CURRENT_TEMP,
    REG_FAN_DURATION,
    REG_FAN_SPEED,
    REG_LIGHT_CONTROL,
    REG_SAUNA_DURATION,
    REG_SAUNA_TYPE,
    REG_SESSION_ACTIVE,
    REG_TARGET_TEMPERATURE,
    STATUS_OFF,
    STATUS_ON,
    FanSpeed,
    SaunaType,
)
from .exceptions import (
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumInvalidDataError,
    SaunumTimeoutError,
)
from .models import SaunumData

__all__ = ["SaunumClient"]

_LOGGER = logging.getLogger(__name__)

_UINT16_MAX = 0x10000
_INT16_SIGN_BIT = 0x8000


def _decode_int16(value: int) -> int:
    """Decode an unsigned 16-bit Modbus register as a signed integer."""
    return value - _UINT16_MAX if value >= _INT16_SIGN_BIT else value


def _validate_registers(name: str, result: Any, expected_count: int) -> list[int]:
    """Validate Modbus register read response length."""
    if result.isError():
        raise SaunumCommunicationError(f"Failed to read {name} registers: {result}")

    registers = getattr(result, "registers", None)
    if registers is None or len(registers) < expected_count:
        actual_count = 0 if registers is None else len(registers)
        raise SaunumInvalidDataError(
            f"Incomplete {name} register data: "
            f"expected {expected_count}, got {actual_count}"
        )

    return cast(list[int], registers)


class SaunumClient:
    """Client for Saunum sauna controller."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        device_id: int = DEFAULT_DEVICE_ID,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Saunum client.

        Args:
            host: IP address or hostname of the sauna controller
            port: Modbus TCP port (default: 502)
            device_id: Modbus device/unit ID (default: 1)
            timeout: Connection timeout in seconds (default: 10)

        Note:
            For production use, prefer using the create() factory method
            which ensures the connection is established before returning.

        Raises:
            ValueError: If host is empty or blank
        """
        if not host or not host.strip():
            raise ValueError("Host must be a non-empty string")

        self._host = host
        self._port = port
        self._device_id = device_id
        self._timeout = timeout
        self._client = AsyncModbusTcpClient(
            host=host,
            port=port,
            timeout=timeout,
        )

    @classmethod
    async def create(
        cls,
        host: str,
        port: int = DEFAULT_PORT,
        device_id: int = DEFAULT_DEVICE_ID,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> SaunumClient:
        """Create and connect a SaunumClient instance.

        This factory method creates a client and ensures it's connected
        before returning. This is the recommended way to create clients
        for production use.

        Args:
            host: IP address or hostname of the sauna controller
            port: Modbus TCP port (default: 502)
            device_id: Modbus device/unit ID (default: 1)
            timeout: Connection timeout in seconds (default: 10)

        Returns:
            Connected SaunumClient instance

        Raises:
            SaunumConnectionError: If connection fails
            SaunumTimeoutError: If connection times out

        Example:
            >>> client = await SaunumClient.create("192.168.1.100")
            >>> # Client is already connected and ready to use
            >>> data = await client.async_get_data()
        """
        _LOGGER.debug("Creating client for %s:%s", host, port)
        client = cls(host=host, port=port, device_id=device_id, timeout=timeout)
        await client.connect()
        _LOGGER.debug("Client created and connected to %s:%s", host, port)
        return client

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    @property
    def port(self) -> int:
        """Return the Modbus TCP port."""
        return self._port

    @property
    def device_id(self) -> int:
        """Return the Modbus device/unit ID."""
        return self._device_id

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected."""
        return bool(self._client.connected)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"SaunumClient({self._host}:{self._port}, connected={self.is_connected})"

    async def connect(self) -> None:
        """Connect to the sauna controller.

        Raises:
            SaunumConnectionError: If connection fails
            SaunumTimeoutError: If connection times out
        """
        try:
            await self._client.connect()
            if not self._client.connected:
                raise SaunumConnectionError(
                    f"Failed to connect to {self._host}:{self._port}"
                )
            _LOGGER.debug("Connected to %s:%s", self._host, self._port)
        except TimeoutError as err:
            _LOGGER.debug("Timeout connecting to %s:%s", self._host, self._port)
            raise SaunumTimeoutError(
                f"Timeout connecting to {self._host}:{self._port}"
            ) from err
        except (OSError, ModbusException) as err:
            _LOGGER.debug("Failed to connect to %s:%s: %s", self._host, self._port, err)
            raise SaunumConnectionError(
                f"Failed to connect to {self._host}:{self._port}: {err}"
            ) from err

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

        _LOGGER.debug("Fetching data from %s:%s", self._host, self._port)

        try:
            # Read control parameters (registers 0-6)
            control_result = await self._client.read_holding_registers(
                address=REG_SESSION_ACTIVE,
                count=7,
                device_id=self._device_id,
            )
            control_regs = _validate_registers(
                "control", control_result, expected_count=7
            )

            # Read status sensors (registers 100-104)
            status_result = await self._client.read_holding_registers(
                address=REG_CURRENT_TEMP,
                count=5,
                device_id=self._device_id,
            )
            status_regs = _validate_registers("status", status_result, expected_count=5)

            # Read alarm status (registers 200-205)
            alarm_result = await self._client.read_holding_registers(
                address=REG_ALARM_DOOR_OPEN,
                count=6,
                device_id=self._device_id,
            )
            alarm_regs = _validate_registers("alarm", alarm_result, expected_count=6)

            # Parse control parameters
            session_active = bool(control_regs[0])
            sauna_type_raw = control_regs[1]
            sauna_type: SaunaType | int = (
                SaunaType(sauna_type_raw)
                if sauna_type_raw in SaunaType
                else sauna_type_raw
            )
            sauna_duration = control_regs[2]
            fan_duration = control_regs[3]

            # Validate target temperature
            target_temp = control_regs[4]
            if target_temp > MAX_TEMPERATURE:
                _LOGGER.warning(
                    "Target temperature %d°C exceeds maximum %d°C",
                    target_temp,
                    MAX_TEMPERATURE,
                )

            fan_speed_raw = control_regs[5]
            fan_speed: FanSpeed | None
            if fan_speed_raw in FanSpeed:
                fan_speed = FanSpeed(fan_speed_raw)
            else:
                _LOGGER.debug(
                    "Invalid fan speed %d received (expected 0-3)", fan_speed_raw
                )
                fan_speed = None
            light_on = bool(control_regs[6])

            # Parse status sensors
            current_temp = float(_decode_int16(status_regs[0]))

            # Combine 32-bit on time from two 16-bit registers
            on_time = (status_regs[1] << 16) | status_regs[2]

            heater_elements_active = status_regs[3]
            door_open = bool(status_regs[4])

            # Parse alarm status
            alarm_door_open = bool(alarm_regs[0])
            alarm_door_sensor = bool(alarm_regs[1])
            alarm_thermal_cutoff = bool(alarm_regs[2])
            alarm_internal_temp = bool(alarm_regs[3])
            alarm_temp_sensor_short = bool(alarm_regs[4])
            alarm_temp_sensor_open = bool(alarm_regs[5])

            data = SaunumData(
                session_active=session_active,
                sauna_type=sauna_type,
                sauna_duration=sauna_duration,
                fan_duration=fan_duration,
                target_temperature=target_temp,
                fan_speed=fan_speed,
                light_on=light_on,
                current_temperature=current_temp,
                on_time=on_time,
                heater_elements_active=heater_elements_active,
                door_open=door_open,
                alarm_door_open=alarm_door_open,
                alarm_door_sensor=alarm_door_sensor,
                alarm_thermal_cutoff=alarm_thermal_cutoff,
                alarm_internal_temp=alarm_internal_temp,
                alarm_temp_sensor_short=alarm_temp_sensor_short,
                alarm_temp_sensor_open=alarm_temp_sensor_open,
            )

            _LOGGER.debug(
                "Data fetched: session=%s, temp=%s°C, target=%s°C, heaters=%s",
                session_active,
                current_temp,
                target_temp,
                heater_elements_active,
            )

            return data

        except TimeoutError as err:
            _LOGGER.debug("Timeout fetching data from %s:%s", self._host, self._port)
            raise SaunumTimeoutError(
                f"Timeout communicating with {self._host}:{self._port}"
            ) from err
        except ModbusException as err:
            _LOGGER.debug("Modbus error fetching data: %s", err)
            raise SaunumCommunicationError(
                f"Modbus communication error: {err}"
            ) from err
        except (IndexError, KeyError, ValueError) as err:
            _LOGGER.debug(
                "Invalid data received from %s:%s: %s", self._host, self._port, err
            )
            raise SaunumInvalidDataError(f"Invalid data received: {err}") from err

    async def async_start_session(self) -> None:
        """Start a sauna session.

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        _LOGGER.debug("Starting sauna session")
        await self._async_write_register(REG_SESSION_ACTIVE, 1)
        _LOGGER.debug("Sauna session started")

    async def async_stop_session(self) -> None:
        """Stop the sauna session.

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        _LOGGER.debug("Stopping sauna session")
        await self._async_write_register(REG_SESSION_ACTIVE, 0)
        _LOGGER.debug("Sauna session stopped")

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

        Note:
            Setting temperature to 0 tells the controller to use the default
            temperature defined for the currently selected sauna type.
        """
        if temperature < 0 or (
            temperature != 0 and not MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE
        ):
            raise ValueError(
                f"Temperature {temperature}°C out of range "
                f"(0=type defined, {MIN_TEMPERATURE}-{MAX_TEMPERATURE}°C)"
            )

        _LOGGER.debug("Setting target temperature to %d°C", temperature)
        await self._async_write_register(REG_TARGET_TEMPERATURE, temperature)
        _LOGGER.debug("Target temperature set to %d°C", temperature)

    async def async_set_sauna_duration(self, minutes: int) -> None:
        """Set the sauna session duration.

        Args:
            minutes: Session duration in minutes.
                - 0: Use sauna type's default duration
                - 1-720: Specific duration in minutes (max 12 hours)

        Raises:
            ValueError: If duration is out of range
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails

        Note:
            Setting duration to 0 tells the controller to use the default
            duration defined for the currently selected sauna type.
        """
        if not MIN_DURATION <= minutes <= MAX_DURATION:
            raise ValueError(
                f"Duration {minutes} minutes out of range "
                f"({MIN_DURATION}-{MAX_DURATION})"
            )

        _LOGGER.debug("Setting sauna duration to %d minutes", minutes)
        await self._async_write_register(REG_SAUNA_DURATION, minutes)
        _LOGGER.debug("Sauna duration set to %d minutes", minutes)

    async def async_set_fan_duration(self, minutes: int) -> None:
        """Set the fan duration.

        Args:
            minutes: Fan duration in minutes.
                - 0: Use sauna type's default fan duration
                - 1-30: Specific fan duration in minutes

        Raises:
            ValueError: If duration is out of range
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails

        Note:
            Setting fan duration to 0 tells the controller to use the default
            fan duration defined for the currently selected sauna type.
        """
        if not MIN_FAN_DURATION <= minutes <= MAX_FAN_DURATION:
            raise ValueError(
                f"Fan duration {minutes} minutes out of range "
                f"({MIN_FAN_DURATION}-{MAX_FAN_DURATION})"
            )

        _LOGGER.debug("Setting fan duration to %d minutes", minutes)
        await self._async_write_register(REG_FAN_DURATION, minutes)
        _LOGGER.debug("Fan duration set to %d minutes", minutes)

    async def async_set_fan_speed(self, speed: int) -> None:
        """Set the fan speed.

        Args:
            speed: Fan speed setting.
                - 0: Fan off
                - 1: Low speed
                - 2: Medium speed
                - 3: High speed

        Raises:
            ValueError: If speed is out of range
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        if speed not in FanSpeed:
            raise ValueError(
                f"Fan speed {speed} out of range ({FanSpeed.OFF}-{FanSpeed.HIGH})"
            )

        _LOGGER.debug("Setting fan speed to %d", speed)
        await self._async_write_register(REG_FAN_SPEED, speed)
        _LOGGER.debug("Fan speed set to %d", speed)

    async def async_set_sauna_type(self, sauna_type: int) -> None:
        """Set the sauna type.

        Args:
            sauna_type: Sauna type setting.
                - 0: Sauna type 1
                - 1: Sauna type 2
                - 2: Sauna type 3

        Raises:
            ValueError: If type is out of range
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails

        Note:
            Each sauna type has predefined defaults for temperature, session
            duration, and fan settings. Refer to your controller's manual for
            specific type configurations.
        """
        if sauna_type not in SaunaType:
            raise ValueError(
                f"Sauna type {sauna_type} invalid. "
                f"Use {SaunaType.TYPE_1}, {SaunaType.TYPE_2}, or {SaunaType.TYPE_3}"
            )

        _LOGGER.debug("Setting sauna type to %d", sauna_type)
        await self._async_write_register(REG_SAUNA_TYPE, sauna_type)
        _LOGGER.debug("Sauna type set to %d", sauna_type)

    async def async_set_light_control(self, enabled: bool) -> None:
        """Set light on/off control.

        Args:
            enabled: True to turn light on, False to turn off

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        value = STATUS_ON if enabled else STATUS_OFF
        _LOGGER.debug("Setting light to %s", "on" if enabled else "off")
        await self._async_write_register(REG_LIGHT_CONTROL, value)
        _LOGGER.debug("Light turned %s", "on" if enabled else "off")

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

        _LOGGER.debug("Writing register %d = %d", address, value)

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

        except TimeoutError as err:
            _LOGGER.debug("Timeout writing register %d", address)
            raise SaunumTimeoutError(
                f"Timeout writing register {address} to {self._host}:{self._port}"
            ) from err
        except ModbusException as err:
            _LOGGER.debug("Modbus error writing register %d: %s", address, err)
            raise SaunumCommunicationError(
                f"Modbus error writing register {address}: {err}"
            ) from err

    async def async_close(self) -> None:
        """Close the connection to the sauna controller."""
        if not self._client.connected:
            _LOGGER.debug("Already disconnected from %s:%s", self._host, self._port)
            return

        _LOGGER.debug("Closing connection to %s:%s", self._host, self._port)
        self._client.close()
        _LOGGER.debug("Disconnected from %s:%s", self._host, self._port)

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.async_close()
