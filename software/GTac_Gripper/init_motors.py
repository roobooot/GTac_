import serial
import time
if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 115200)
    time.sleep(0.5)
    if ser.is_open:
        print('Serial Port Opened:\n', ser)
        ser.flushInput()
    ser.write(b'<>')
    # ser.write(b'<2100>')
    # ser.write(b'<1100>')
    ser.close()