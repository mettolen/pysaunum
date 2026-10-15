"""Data models for Saunum sauna controller."""

from __future__ import annotations

from dataclasses import dataclass

from .const import (
    ControllerState,
    FanSpeed,
    Notification,
    SaunaType,
    StartBlockReason,
)

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
    """Device-dependent preset index, with a SaunaType label when available."""

    sauna_duration: int
    """Session duration in minutes (60-1080), or 0 for sauna type default."""

    fan_duration: int
    """Fan duration in minutes (1-20), or 0 for sauna type default."""

    target_temperature: int
    """Target temperature in Celsius, or 0 for a type default or cooldown."""

    fan_speed: FanSpeed | None
    """Fan speed enum member, or None if the raw value was unrecognized."""

    light_on: bool
    """Whether the light is on."""

    # Status sensors
    current_temperature: int
    """Current temperature in Celsius, 1°C resolution."""

    on_time: int
    """Device total on time in seconds since last reset."""

    heater_elements_active: int
    """Number of heater elements currently active."""

    door_open: bool
    """Whether the door is open."""

    humidity: int
    """Relative humidity percentage."""

    active_session_duration: int
    """Active session duration in minutes, or 0 when inactive."""

    session_time_remaining: int
    """Time remaining in the active session in seconds."""

    fan_time_remaining: int
    """Fan runtime remaining in seconds."""

    controller_state: ControllerState
    """Operating state reported by the controller."""

    autoleil_connected: bool
    """Whether AutoLeil is connected."""

    autoleil_active: bool
    """Whether AutoLeil is active."""

    autoleil_button_presses: int
    """Physical AutoLeil button press count."""

    autoleil_manual_throws: int
    """Manual AutoLeil water throw count."""

    autoleil_auto_throws: int
    """Automatic AutoLeil water throw count."""

    active_notifications: Notification
    """Active controller notifications."""

    start_block_reasons: StartBlockReason
    """Conditions preventing a session from starting."""

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

    @property
    def session_state(self) -> ControllerState:
        """Return the device-reported state for compatibility."""
        return self.controller_state

    @property
    def can_start_session(self) -> bool:
        """Return whether no controller condition blocks session start."""
        return not self.start_block_reasons
