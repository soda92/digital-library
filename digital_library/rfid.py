import serial

try:
    ser = serial.Serial('COM3', 9600, timeout=1)  # Replace 'COM3' with your port
    print(f"Connected to serial port: {ser.name}")

    # Send a command to the RFID reader (e.g., to read a tag)
    # This will be specific to your reader's protocol
    ser.write(b'\x01\x02\x03\x04') # Example: send some bytes

    response = ser.read(100) # Read up to 100 bytes
    if response:
        print(f"RFID reader response: {response.hex()}")
        # Parse the response to extract tag data (e.g., EPC, user memory)
    else:
        print("No response from RFID reader.")

except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed.")