import serial
import time

# Replace with your actual port
ser = serial.Serial("/dev/cu.usbserial-1130", 115200, timeout=1)
time.sleep(2)  # Wait for connection

ser.write(b"HIGH\n")
time.sleep(1)
print(ser.readline().decode().strip())

ser.write(b"LOW\n")  
time.sleep(1)
print(ser.readline().decode().strip())

ser.close()