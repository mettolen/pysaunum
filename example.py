"""Example usage of pysaunum library."""

import asyncio

from pysaunum import SaunumClient, SaunumCommunicationError, SaunumConnectionError
from pysaunum.const import (
    DEFAULT_DURATION,
    FAN_SPEED_HIGH,
    FAN_SPEED_LOW,
    FAN_SPEED_MEDIUM,
    FAN_SPEED_OFF,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_TEMPERATURE,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_TEMPERATURE,
    SAUNA_TYPE_1,
    SAUNA_TYPE_2,
    SAUNA_TYPE_3,
)


async def main():
    """Example main function demonstrating all pysaunum features."""
    # Create client - replace with your sauna controller's IP
    client = SaunumClient(host="192.168.1.100", port=502, device_id=1)

    try:
        # Connect to the sauna controller
        print("Connecting to sauna controller...")
        await client.connect()
        print("Connected!")

        # Read current state
        print("\nReading current state...")
        data = await client.async_get_data()
        print(f"  Current temperature: {data.current_temperature}°C")
        print(f"  Target temperature: {data.target_temperature}°C")
        print(f"  Session active: {data.session_active}")
        print(f"  Heater elements active: {data.heater_elements_active}")
        fan_speed_names = ["Off", "Low", "Medium", "High"]
        if data.fan_speed is not None and 0 <= data.fan_speed <= 3:
            fan_name = fan_speed_names[data.fan_speed]
        else:
            fan_name = "Unknown"
        print(f"  Fan speed: {data.fan_speed} ({fan_name})")
        print(f"  Sauna type: {data.sauna_type}")
        print(f"  Session duration: {data.sauna_duration} minutes")

        # Example: Configure sauna settings
        print("\nConfiguring sauna settings...")

        # Set sauna type (0=Type 1, 1=Type 2, 2=Type 3)
        print(f"Setting sauna type to Type 2 (value {SAUNA_TYPE_2})...")
        await client.async_set_sauna_type(SAUNA_TYPE_2)

        # Set target temperature (0 to turn off, or 40-100°C)
        print("Setting target temperature to 85°C...")
        await client.async_set_target_temperature(85)

        # Set session duration (0-720 minutes, default 120)
        print(f"Setting session duration to {DEFAULT_DURATION} minutes...")
        await client.async_set_sauna_duration(DEFAULT_DURATION)

        # Set fan speed (0=Off, 1=Low, 2=Medium, 3=High)
        print(f"Setting fan speed to Medium (value {FAN_SPEED_MEDIUM})...")
        await client.async_set_fan_speed(FAN_SPEED_MEDIUM)

        # Set fan duration (0-30 minutes, 0=continuous)
        print("Setting fan duration to 15 minutes...")
        await client.async_set_fan_duration(15)

        # Start a sauna session
        print("\nStarting sauna session...")
        await client.async_start_session()

        # Read updated state
        print("\nReading updated state after configuration...")
        data = await client.async_get_data()
        print(f"  Current temperature: {data.current_temperature}°C")
        print(f"  Target temperature: {data.target_temperature}°C")
        print(f"  Session active: {data.session_active}")
        print(f"  Heater elements active: {data.heater_elements_active}/3")
        print(f"  Fan speed: {data.fan_speed}")
        print(f"  Sauna type: {data.sauna_type}")
        print(f"  Session duration: {data.sauna_duration} minutes")

        # Demonstrate fan speed control
        print("\nDemonstrating fan speed control...")
        for speed, name in [
            (FAN_SPEED_OFF, "Off"),
            (FAN_SPEED_LOW, "Low"),
            (FAN_SPEED_HIGH, "High"),
            (FAN_SPEED_OFF, "Off"),
        ]:
            print(f"Setting fan to {name}...")
            await client.async_set_fan_speed(speed)
            await asyncio.sleep(1)  # Small delay for demonstration

        # Demonstrate zero value support
        print("\nDemonstrating zero value support...")
        print("Setting temperature to 0 (heater off)...")
        await client.async_set_target_temperature(0)

        print("Setting fan duration to 0 (continuous)...")
        await client.async_set_fan_duration(0)

        # Stop the session
        print("\nStopping session...")
        await client.async_stop_session()

        # Demonstrate light control
        print("\nTesting light control...")
        await client.async_set_light_control(True)
        print("Light turned on")
        await asyncio.sleep(2)
        await client.async_set_light_control(False)
        print("Light turned off")

    except SaunumConnectionError as err:
        print(f"Connection error: {err}")
    except SaunumCommunicationError as err:
        print(f"Communication error: {err}")
    finally:
        # Close the connection (now synchronous)
        client.close()
        print("\nDisconnected.")


async def main_with_context_manager():
    """Example using async context manager (recommended approach)."""
    print("\n" + "=" * 50)
    print("CONTEXT MANAGER EXAMPLE")
    print("=" * 50)

    try:
        async with SaunumClient(host="192.168.1.100") as client:
            # Get current state
            data = await client.async_get_data()
            print(f"Current temperature: {data.current_temperature}°C")
            print(f"Target temperature: {data.target_temperature}°C")
            print(f"Heater elements active: {data.heater_elements_active}")

            # Quick session example
            if not data.session_active:
                print("\nStarting quick session...")
                await client.async_set_target_temperature(80)
                await client.async_set_sauna_duration(60)  # 1 hour
                await client.async_start_session()
                print("Session started!")
            else:
                print("Session already active")

    except (SaunumConnectionError, SaunumCommunicationError) as err:
        print(f"Error: {err}")


async def demonstrate_constants():
    """Demonstrate available constants and their values."""
    print("\n" + "=" * 50)
    print("AVAILABLE CONSTANTS")
    print("=" * 50)

    print("Fan Speed Constants:")
    print(f"  FAN_SPEED_OFF = {FAN_SPEED_OFF}")
    print(f"  FAN_SPEED_LOW = {FAN_SPEED_LOW}")
    print(f"  FAN_SPEED_MEDIUM = {FAN_SPEED_MEDIUM}")
    print(f"  FAN_SPEED_HIGH = {FAN_SPEED_HIGH}")

    print("\nSauna Type Constants (0-indexed):")
    print(f"  SAUNA_TYPE_1 = {SAUNA_TYPE_1}")
    print(f"  SAUNA_TYPE_2 = {SAUNA_TYPE_2}")
    print(f"  SAUNA_TYPE_3 = {SAUNA_TYPE_3}")

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

    print("\nExample completed! 🚀")
