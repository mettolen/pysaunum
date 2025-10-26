"""Data models for Saunum sauna controller."""

from dataclasses import dataclass


@dataclass
class SaunumData:
    """Data from Saunum sauna controller.

    All temperatures are in Celsius (device native unit).
    All durations are in minutes unless otherwise specified.
    """

    # Session control parameters
    session_active: bool
    """Whether a sauna session is currently active."""

    sauna_type: int | None
    """Sauna type (0, 1, or 2), or None if not available."""

    sauna_duration: int | None
    """Session duration in minutes (0-720), or None if not set."""

    fan_duration: int | None
    """Fan duration in minutes (0-30), or None if not set."""

    target_temperature: int | None
    """Target temperature in Celsius (40-100), or None if not set."""

    fan_speed: int | None
    """Fan speed (0=Off, 1=Low, 2=Medium, 3=High), or None if not available."""

    light_on: bool | None
    """Whether the light is on, or None if not available."""

    # Status sensors
    current_temperature: float | None
    """Current temperature in Celsius, 1°C resolution, or None if not available."""

    on_time: int | None
    """Device total on time in seconds since last reset, or None if not available."""

    heater_elements_active: int | None
    """Number of heater elements currently active (0-3), or None if not available."""

    door_open: bool | None
    """Whether the door is open, or None if not available."""

    # Alarm status
    alarm_door_open: bool | None
    """Alarm: door open during heating, or None if not available."""

    alarm_door_sensor: bool | None
    """Alarm: door open too long, or None if not available."""

    alarm_thermal_cutoff: bool | None
    """Alarm: thermal cutoff activated, or None if not available."""

    alarm_internal_temp: bool | None
    """Alarm: internal temperature overheating, or None if not available."""

    alarm_temp_sensor_short: bool | None
    """Alarm: temperature sensor shorted, or None if not available."""

    alarm_temp_sensor_open: bool | None
    """Alarm: temperature sensor not connected, or None if not available."""
