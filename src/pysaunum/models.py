"""Data models for Saunum sauna controller."""

from dataclasses import dataclass

from .const import FanSpeed, SaunaType

__all__ = ["SaunumData"]


@dataclass(frozen=True)
class SaunumData:
    """Data from Saunum sauna controller.

    All temperatures are in Celsius (device native unit).
    All durations are in minutes unless otherwise specified.
    """

    # Session control parameters
    session_active: bool
    """Whether a sauna session is currently active."""

    sauna_type: SaunaType | int
    """Sauna type. A SaunaType enum member for known types, or raw int for unknown."""

    sauna_duration: int | None
    """Session duration in minutes (0-720), or None if not set."""

    fan_duration: int | None
    """Fan duration in minutes (0-30), or None if not set."""

    target_temperature: int | None
    """Target temperature in Celsius (40-100), or None if not set."""

    fan_speed: FanSpeed | None
    """Fan speed enum member, or None if the raw value was unrecognized."""

    light_on: bool
    """Whether the light is on."""

    # Status sensors
    current_temperature: float
    """Current temperature in Celsius, 1°C resolution."""

    on_time: int
    """Device total on time in seconds since last reset."""

    heater_elements_active: int
    """Number of heater elements currently active."""

    door_open: bool
    """Whether the door is open."""

    # Alarm status
    alarm_door_open: bool
    """Alarm: door open during heating."""

    alarm_door_sensor: bool
    """Alarm: door open too long."""

    alarm_thermal_cutoff: bool
    """Alarm: thermal cutoff activated."""

    alarm_internal_temp: bool
    """Alarm: internal temperature overheating."""

    alarm_temp_sensor_short: bool
    """Alarm: temperature sensor shorted."""

    alarm_temp_sensor_open: bool
    """Alarm: temperature sensor not connected."""
