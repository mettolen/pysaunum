"""Example usage of pysaunum library."""

import asyncio

from pysaunum import (
    SaunumClient,
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumData,
    SaunumTimeoutError,
)
from pysaunum.const import (
    DEFAULT_DURATION,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_TEMPERATURE,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_TEMPERATURE,
    FanSpeed,
    SaunaType,
)

HOST = "192.168.1.143"


def _print_state(data: SaunumData) -> None:
    """Print the full sauna state."""
    fan_name = (
        data.fan_speed.name.capitalize() if data.fan_speed is not None else "Unknown"
    )
    sauna_type_name = (
        data.sauna_type.name
        if isinstance(data.sauna_type, SaunaType)
        else f"Unknown({data.sauna_type})"
    )

    print(f"  Current temperature: {data.current_temperature}°C")
    print(f"  Target temperature:  {data.target_temperature}°C")
    print(f"  Session active:      {data.session_active}")
    print(f"  Heater elements:     {data.heater_elements_active}")
    print(f"  Fan speed:           {data.fan_speed} ({fan_name})")
    print(f"  Sauna type:          {data.sauna_type} ({sauna_type_name})")
    print(f"  Session duration:    {data.sauna_duration} minutes")
    print(f"  Fan duration:        {data.fan_duration} minutes")
    print(f"  Light on:            {data.light_on}")
    print(f"  Door open:           {data.door_open}")
    print(f"  On time:             {data.on_time} seconds")

    # Alarm summary
    alarms = [
        ("Door open", data.alarm_door_open),
        ("Door sensor", data.alarm_door_sensor),
        ("Thermal cutoff", data.alarm_thermal_cutoff),
        ("Internal temp", data.alarm_internal_temp),
        ("Temp sensor short", data.alarm_temp_sensor_short),
        ("Temp sensor open", data.alarm_temp_sensor_open),
    ]
    active_alarms = [name for name, active in alarms if active]
    if active_alarms:
        print(f"  Active alarms:       {', '.join(active_alarms)}")
    else:
        print("  Active alarms:       None")


async def main() -> None:
    """Example main function demonstrating all pysaunum features."""
    # Create and connect using the factory method (recommended)
    print("Connecting to sauna controller...")
    client = await SaunumClient.create(host=HOST)
    print(f"Connected! ({client!r})")

    try:
        # Read current state
        print("\nReading current state...")
        data = await client.async_get_data()
        _print_state(data)

        # Example: Configure sauna settings
        print("\nConfiguring sauna settings...")

        # Set sauna type (0=Type 1, 1=Type 2, 2=Type 3)
        print(f"Setting sauna type to Type 2 (value {SaunaType.TYPE_2})...")
        await client.async_set_sauna_type(SaunaType.TYPE_2)

        # Set target temperature (0 for type default, or 40-100°C)
        print("Setting target temperature to 85°C...")
        await client.async_set_target_temperature(85)

        # Set session duration (0-720 minutes, 0 for type default)
        print(f"Setting session duration to {DEFAULT_DURATION} minutes...")
        await client.async_set_sauna_duration(DEFAULT_DURATION)

        # Set fan speed (0=Off, 1=Low, 2=Medium, 3=High)
        print(f"Setting fan speed to Medium ({FanSpeed.MEDIUM})...")
        await client.async_set_fan_speed(FanSpeed.MEDIUM)

        # Set fan duration (0-30 minutes, 0 for type default)
        print("Setting fan duration to 15 minutes...")
        await client.async_set_fan_duration(15)

        # Start a sauna session
        print("\nStarting sauna session...")
        await client.async_start_session()

        await asyncio.sleep(2)

        # Read updated state
        print("\nReading updated state after configuration...")
        data = await client.async_get_data()
        _print_state(data)

        # Demonstrate fan speed control
        print("\nDemonstrating fan speed control...")
        for speed in (FanSpeed.OFF, FanSpeed.LOW, FanSpeed.HIGH, FanSpeed.OFF):
            print(f"Setting fan to {speed.name.capitalize()}...")
            await client.async_set_fan_speed(speed)
            await asyncio.sleep(2)

        # Stop the session
        print("\nStopping session...")
        await client.async_stop_session()

        await asyncio.sleep(2)

        # Demonstrate light control
        print("\nTesting light control...")
        await client.async_set_light_control(True)
        print("Light turned on")
        await asyncio.sleep(2)
        await client.async_set_light_control(False)
        print("Light turned off")

    except SaunumConnectionError as err:
        print(f"Connection error: {err}")
    except SaunumTimeoutError as err:
        print(f"Timeout error: {err}")
    except SaunumCommunicationError as err:
        print(f"Communication error: {err}")
    finally:
        # Always stop the session and turn off the light before disconnecting
        try:
            await client.async_stop_session()
            await client.async_set_light_control(False)
            print("Sauna session stopped and light turned off")
        except (SaunumConnectionError, SaunumTimeoutError, SaunumCommunicationError):
            print("Warning: could not stop session during cleanup")
        await client.async_close()
        print("Disconnected.")


async def main_with_context_manager() -> None:
    """Example using async context manager (recommended approach)."""
    print("\n" + "=" * 50)
    print("CONTEXT MANAGER EXAMPLE")
    print("=" * 50)

    try:
        async with SaunumClient(host=HOST) as client:
            data = await client.async_get_data()
            _print_state(data)

            # Quick session example
            if not data.session_active:
                print("\nStarting quick session...")
                await client.async_set_target_temperature(80)
                await client.async_set_sauna_duration(60)  # 1 hour
                await client.async_start_session()
                print("Session started!")

                await asyncio.sleep(2)

                # Stop the session before exiting
                print("Stopping session...")
                await client.async_stop_session()
                print("Session stopped.")
            else:
                print("Session already active, stopping it...")
                await client.async_stop_session()
                print("Session stopped.")

    except (SaunumConnectionError, SaunumTimeoutError, SaunumCommunicationError) as err:
        print(f"Error: {err}")


async def demonstrate_constants() -> None:
    """Demonstrate available constants and their values."""
    print("\n" + "=" * 50)
    print("AVAILABLE CONSTANTS")
    print("=" * 50)

    print("Fan Speed Constants:")
    for speed in FanSpeed:
        print(f"  FanSpeed.{speed.name} = {speed.value}")

    print("\nSauna Type Constants:")
    for sauna_type in SaunaType:
        print(f"  SaunaType.{sauna_type.name} = {sauna_type.value}")

    print("\nTemperature Limits:")
    print(f"  MIN_TEMPERATURE = {MIN_TEMPERATURE}°C")
    print(f"  MAX_TEMPERATURE = {MAX_TEMPERATURE}°C")

    print("\nDuration Limits:")
    print(f"  MIN_DURATION = {MIN_DURATION} minutes")
    print(f"  MAX_DURATION = {MAX_DURATION} minutes")
    print(f"  DEFAULT_DURATION = {DEFAULT_DURATION} minutes")

    print("\nFan Duration Limits:")
    print(f"  MIN_FAN_DURATION = {MIN_FAN_DURATION} minutes")
    print(f"  MAX_FAN_DURATION = {MAX_FAN_DURATION} minutes")


if __name__ == "__main__":
    print("PYSAUNUM LIBRARY EXAMPLE")
    print("=" * 50)

    # Show available constants
    asyncio.run(demonstrate_constants())

    # Run the full example
    print("\nFULL FEATURE DEMONSTRATION")
    print("=" * 50)
    asyncio.run(main())

    # Run context manager example
    asyncio.run(main_with_context_manager())

    print("\nExample completed!")
