"""Data models for Saunum sauna controller."""

from dataclasses import dataclass

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

    sauna_type: int
    """Sauna type (0, 1, or 2)."""

    sauna_duration: int | None
    """Session duration in minutes (0-720), or None if not set."""

    fan_duration: int | None
    """Fan duration in minutes (0-30), or None if not set."""

    target_temperature: int | None
    """Target temperature in Celsius (40-100), or None if not set."""

    fan_speed: int | None
    """Fan speed (0=Off, 1=Low, 2=Medium, 3=High), or None if not available."""

    light_on: bool
    """Whether the light is on."""

    # Status sensors
    current_temperature: float
    """Current temperature in Celsius, 1°C resolution."""

    on_time: int
    """Device total on time in seconds since last reset."""

    heater_elements_active: int | None
    """Number of heater elements currently active (0-3), or None if not available."""

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
