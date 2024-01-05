import serial
import time

# Replace 'COM3' with the actual name of your serial port
ser = serial.Serial('COM5', baudrate=115200, timeout=1)

try:
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(f"Received data: {line}")
        time.sleep(0.1)  # Adjust the sleep time based on your requirements

except KeyboardInterrupt:
    print("Serial reading stopped by the user.")

finally:
    ser.close()
