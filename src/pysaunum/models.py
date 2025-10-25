"""Data models for Saunum sauna controller."""

from dataclasses import dataclass


@dataclass
class SaunumData:
    """Data from Saunum sauna controller.
    
    All temperatures are in Celsius (device native unit).
    """

    session_active: bool
    """Whether a sauna session is currently active."""

    target_temperature: int | None
    """Target temperature in Celsius, or None if not set."""

    current_temperature: float | None
    """Current temperature in Celsius, or None if not available."""

    heater_on: bool
    """Whether the heater is currently on."""
