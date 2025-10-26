"""Saunum sauna controller client."""

from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_FAN_SPEED,
    MAX_TEMPERATURE,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_FAN_SPEED,
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
    SAUNA_TYPE_1,
    SAUNA_TYPE_2,
    SAUNA_TYPE_3,
    STATUS_OFF,
    STATUS_ON,
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
            _LOGGER.info("Connected to %s:%s", self._host, self._port)
        except (OSError, ModbusException) as err:
            _LOGGER.debug("Failed to connect to %s:%s: %s", self._host, self._port, err)
            raise SaunumConnectionError(
                f"Failed to connect to {self._host}:{self._port}: {err}"
            ) from err

    def close(self) -> None:
        """Close the connection to the sauna controller."""
        if self._client.connected:
            self._client.close()
            _LOGGER.info("Closed connection to %s:%s", self._host, self._port)

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
            # Read control parameters (registers 0-6)
            control_result = await self._client.read_holding_registers(
                address=REG_SESSION_ACTIVE,
                count=7,
                device_id=self._device_id,
            )
            if control_result.isError():
                raise SaunumCommunicationError(
                    f"Failed to read control registers: {control_result}"
                )

            # Read status sensors (registers 100-104)
            status_result = await self._client.read_holding_registers(
                address=REG_CURRENT_TEMP,
                count=5,
                device_id=self._device_id,
            )
            if status_result.isError():
                raise SaunumCommunicationError(
                    f"Failed to read status registers: {status_result}"
                )

            # Read alarm status (registers 200-205)
            alarm_result = await self._client.read_holding_registers(
                address=REG_ALARM_DOOR_OPEN,
                count=6,
                device_id=self._device_id,
            )
            if alarm_result.isError():
                raise SaunumCommunicationError(
                    f"Failed to read alarm registers: {alarm_result}"
                )

            control_regs = control_result.registers
            status_regs = status_result.registers
            alarm_regs = alarm_result.registers

            # Parse control parameters
            session_active = bool(control_regs[0])
            sauna_type = control_regs[1] if control_regs[1] >= 0 else None
            sauna_duration = control_regs[2] if control_regs[2] > 0 else None
            fan_duration = control_regs[3] if control_regs[3] > 0 else None

            # Validate target temperature
            target_temp_raw = control_regs[4]
            target_temp: int | None = None
            if target_temp_raw >= MIN_TEMPERATURE:
                if target_temp_raw > MAX_TEMPERATURE:
                    _LOGGER.warning(
                        "Target temperature %d°C exceeds maximum %d°C",
                        target_temp_raw,
                        MAX_TEMPERATURE,
                    )
                target_temp = target_temp_raw
            elif target_temp_raw != 0:
                _LOGGER.debug(
                    "Invalid target temperature %d received (expected 0 or %d-%d)",
                    target_temp_raw,
                    MIN_TEMPERATURE,
                    MAX_TEMPERATURE,
                )

            fan_speed_raw = control_regs[5]
            if 0 <= fan_speed_raw <= 3:
                fan_speed = fan_speed_raw
            else:
                _LOGGER.debug(
                    "Invalid fan speed %d received (expected 0-3)", fan_speed_raw
                )
                fan_speed = None
            light_on = bool(control_regs[6]) if control_regs[6] >= 0 else None

            # Parse status sensors
            current_temp = float(status_regs[0]) if status_regs[0] >= 0 else None

            # Combine 32-bit on time from two 16-bit registers
            on_time_high = status_regs[1]
            on_time_low = status_regs[2]
            on_time = (
                (on_time_high << 16) | on_time_low
                if on_time_high >= 0 and on_time_low >= 0
                else None
            )

            heater_elements_raw = status_regs[3]
            if 0 <= heater_elements_raw <= 3:
                heater_elements_active = heater_elements_raw
            else:
                _LOGGER.debug(
                    "Invalid heater elements count %d received (expected 0-3)",
                    heater_elements_raw,
                )
                heater_elements_active = None
            door_open = bool(status_regs[4]) if status_regs[4] >= 0 else None

            # Parse alarm status
            alarm_door_open = bool(alarm_regs[0]) if alarm_regs[0] >= 0 else None
            alarm_door_sensor = bool(alarm_regs[1]) if alarm_regs[1] >= 0 else None
            alarm_thermal_cutoff = bool(alarm_regs[2]) if alarm_regs[2] >= 0 else None
            alarm_internal_temp = bool(alarm_regs[3]) if alarm_regs[3] >= 0 else None
            alarm_temp_sensor_short = (
                bool(alarm_regs[4]) if alarm_regs[4] >= 0 else None
            )
            alarm_temp_sensor_open = bool(alarm_regs[5]) if alarm_regs[5] >= 0 else None

            return SaunumData(
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

        await self._async_write_register(REG_TARGET_TEMPERATURE, temperature)

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

        await self._async_write_register(REG_SAUNA_DURATION, minutes)

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
        if minutes < 0 or minutes > MAX_FAN_DURATION:
            raise ValueError(
                f"Fan duration {minutes} minutes out of range "
                f"({MIN_FAN_DURATION}-{MAX_FAN_DURATION})"
            )

        await self._async_write_register(REG_FAN_DURATION, minutes)

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
        if not MIN_FAN_SPEED <= speed <= MAX_FAN_SPEED:
            raise ValueError(
                f"Fan speed {speed} out of range ({MIN_FAN_SPEED}-{MAX_FAN_SPEED})"
            )

        await self._async_write_register(REG_FAN_SPEED, speed)

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
        if sauna_type not in (SAUNA_TYPE_1, SAUNA_TYPE_2, SAUNA_TYPE_3):
            raise ValueError(
                f"Sauna type {sauna_type} invalid. "
                f"Use {SAUNA_TYPE_1}, {SAUNA_TYPE_2}, or {SAUNA_TYPE_3}"
            )

        await self._async_write_register(REG_SAUNA_TYPE, sauna_type)

    async def async_set_light_control(self, enabled: bool) -> None:
        """Set light on/off control.

        Args:
            enabled: True to turn light on, False to turn off

        Raises:
            SaunumConnectionError: If not connected
            SaunumCommunicationError: If write operation fails
        """
        value = STATUS_ON if enabled else STATUS_OFF
        await self._async_write_register(REG_LIGHT_CONTROL, value)

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
        self.close()
