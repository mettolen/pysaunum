"""Tests for pysaunum data models."""

import pytest

from pysaunum import (
    ControllerState,
    FanSpeed,
    Notification,
    SaunumData,
    StartBlockReason,
)


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
        humidity=45,
        active_session_duration=0,
        session_time_remaining=0,
        fan_time_remaining=0,
        controller_state=ControllerState.STANDBY,
        autoleil_connected=True,
        autoleil_active=False,
        autoleil_button_presses=5,
        autoleil_manual_throws=3,
        autoleil_auto_throws=7,
        active_notifications=Notification(0),
        start_block_reasons=StartBlockReason(0),
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
    assert data.can_start_session is True


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
