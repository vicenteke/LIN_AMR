from machine import Pin, UART
from utime import sleep
from lin import LINMaster

if __name__ == '__main__':
    LIN_RFID         = 2
    LIN_SERVO_OPEN   = 3
    LIN_SERVO_CLOSE  = 4
    LIN_SERVO_STATUS = 5


    SERVO_OPEN   = 0
    SERVO_CLOSED = 1

    sleep(2)
    lin = LINMaster()
    servo_status = 0
    servo_next_operation = SERVO_CLOSED

    RIGHT_RFID_TAG = [188, 228, 19, 49]

    while True:
        servo_status = lin.send_header(LIN_SERVO_STATUS)[0]
        if servo_next_operation == servo_status:
            if servo_next_operation == SERVO_CLOSED:
                print("Cage already attached!")
                servo_next_operation = SERVO_OPEN
            else:
                print("Cage already dettached!")
                servo_next_operation = SERVO_CLOSED
        else:
            read_rfid = lin.send_header(LIN_RFID)
            if read_rfid != RIGHT_RFID_TAG:
                print("Invalid RFID:", read_rfid if read_rfid != [-1] else "communication fail")
            elif servo_next_operation == SERVO_CLOSED:
                print("RFID tag identified, attaching cage...")
                servo_status = lin.send_header(LIN_SERVO_CLOSE)[0]
                servo_next_operation = SERVO_OPEN
            else:
                print("RFID tag identified, dettaching cage...")
                servo_status = lin.send_header(LIN_SERVO_OPEN)[0]
                servo_next_operation = SERVO_CLOSED

            print("STATUS:", "Attached" if servo_status == SERVO_CLOSED else "Dettached")

        sleep(5)
