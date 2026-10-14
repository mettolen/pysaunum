"""Tests for pysaunum data models."""

from dataclasses import replace

import pytest

from pysaunum import FanSpeed, SaunaSessionState, SaunumData


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
        alarm_door_open=False,
        alarm_door_sensor=False,
        alarm_thermal_cutoff=False,
        alarm_internal_temp=False,
        alarm_temp_sensor_short=False,
        alarm_temp_sensor_open=False,
    )


@pytest.mark.parametrize(
    ("session_active", "target_temperature", "expected_state"),
    [
        (False, 0, SaunaSessionState.INACTIVE),
        (False, 80, SaunaSessionState.INACTIVE),
        (True, 0, SaunaSessionState.COOLDOWN),
        (True, 80, SaunaSessionState.HEATING),
    ],
)
def test_session_state(
    session_active: bool,
    target_temperature: int,
    expected_state: SaunaSessionState,
) -> None:
    """Test normalization of raw session and target-temperature registers."""
    data = replace(
        _create_sauna_data(),
        session_active=session_active,
        target_temperature=target_temperature,
    )

    assert data.session_state is expected_state
