"""Tests for pysaunum data models."""

import pytest

from pysaunum import ControllerState, FanSpeed, SaunumData


def _create_sauna_data() -> SaunumData:
    """Return representative sauna data."""
    return SaunumData(
        session_active=False,
        sauna_type=0,
        sauna_duration=120,
        fan_duration=10,
        target_temperature=80,
        fan_speed=FanSpeed.MEDIUM,
        light_on=False,
        current_temperature=75,
        on_time=3600,
        heater_elements_active=0,
        door_open=False,
        controller_state=ControllerState.STANDBY,
        alarm_door_open=False,
        alarm_door_sensor=False,
        alarm_thermal_cutoff=False,
        alarm_internal_temp=False,
        alarm_temp_sensor_short=False,
        alarm_temp_sensor_open=False,
    )


def test_session_state() -> None:
    """Test the compatibility alias for the device-reported controller state."""
    data = _create_sauna_data()

    assert data.session_state is ControllerState.STANDBY


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, ControllerState.STANDBY),
        (2, ControllerState.SCHEDULED),
        (3, ControllerState.HEATING),
        (4, ControllerState.READY),
        (5, ControllerState.COOLDOWN),
        (6, ControllerState.WAITING_FOR_DOOR),
    ],
)
def test_controller_state(value: int, expected: ControllerState) -> None:
    """Test controller state register mappings."""
    assert ControllerState(value) is expected
