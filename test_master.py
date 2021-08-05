from machine import Pin, UART
from utime import sleep
from lin import LINMaster

if __name__ == '__main__':
    LIN_RFID  = 2
    LIN_SERVO = 3

    sleep(2)
    lin = LINMaster()
    servo_result = 0

    while True:
        read_rfid = lin.send_header(LIN_RFID)[0]
        print("Received: ", read_rfid)
        sleep(3)
