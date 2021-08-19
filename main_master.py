import sys
import select
from machine import Pin, UART
from utime import sleep
from lin import LINMaster


class MainMaster():
    LIN_RFID         = 2
    LIN_SERVO_OPEN   = 3
    LIN_SERVO_CLOSE  = 4
    LIN_SERVO_STATUS = 5

    SERVO_OPEN   = 0
    SERVO_CLOSED = 1

    RIGHT_RFID_TAG = [188, 228, 19, 49]

    def __init__(self):
        self.lin = LINMaster()
        self.servo_status = 0
        self.servo_next_operation = self.SERVO_CLOSED
        self.poll = select.poll()
        self.poll.register(sys.stdin, select.POLLIN)

    def ask_rfid(self):
        return self.lin.send_header(self.LIN_RFID)

    def ask_status(self):
        return self.lin.send_header(self.LIN_SERVO_STATUS)[0]

    def ask_open(self):
        last_status = self.servo_status
        self.servo_status = self.ask_status()

        if self.servo_status == -1:
            self.servo_status = last_status
            return False
        elif self.servo_status == self.SERVO_OPEN:
            print("Cage already dettached!")
            return True

        read_rfid = self.ask_rfid()
        if read_rfid != self.RIGHT_RFID_TAG:
            print("Invalid RFID:", read_rfid if read_rfid != [-1] else "communication fail")
            return False
        else:
            print("RFID tag identified, dettaching cage...")
            self.servo_status = self.lin.send_header(self.LIN_SERVO_OPEN)[0]
            return True

    def ask_close(self):
        last_status = self.servo_status
        self.servo_status = self.ask_status()

        if self.servo_status == -1:
            self.servo_status = last_status
            return False
        elif self.servo_status == self.SERVO_CLOSED:
            print("Cage already attached!")
            return True

        read_rfid = self.ask_rfid()
        if read_rfid != self.RIGHT_RFID_TAG:
            print("Invalid RFID:", read_rfid if read_rfid != [-1] else "communication fail")
            return False
        else:
            print("RFID tag identified, attaching cage...")
            self.servo_status = self.lin.send_header(self.LIN_SERVO_CLOSE)[0]
            return True

    def print_status(self):
        print("STATUS:",
            "Attached" if self.servo_status == self.SERVO_CLOSED else "Dettached",
            "\n")

    def display_help(self):
        print("Help:\n")
        print("'r' - read RFID")
        print("'a' - dettach cage")
        print("'f' - attach cage")
        print("'p' - start periodic execution")
        print("'h' - display help")
        print("\n")

    def periodic_function(self):
        try:
            print("Periodic function started")
            print("Use Ctrl+C to stop.\n")
            while True:
                if self.servo_next_operation == self.SERVO_OPEN:
                    if self.ask_open():
                        self.servo_next_operation = self.SERVO_CLOSED
                else:
                    if self.ask_close():
                        self.servo_next_operation = self.SERVO_OPEN

                self.print_status()
                sleep(5)

        except KeyboardInterrupt:
            print("Periodic function stopped!\n")
            return

    def run(self):
        self.display_help()
        while True:
            serial = self.poll.poll()        
            _input = serial[0][0].read(1)

            if _input == 'r':
                print("'r' - read RFID")
                read_rfid = self.ask_rfid()
                if read_rfid == [-1]:
                    print("Error during RFID identification...\n")
                else:
                    print("RFID:", read_rfid, "\n")

            elif _input == 'a':
                print("'a' - dettach cage")
                self.ask_open()
                self.print_status()

            elif _input == 'f':
                print("'f' - attach cage")
                self.ask_close()
                self.print_status()

            elif _input == 'p':
                print("'p' - start periodic execution")
                self.periodic_function()
                self.display_help()

            elif _input == 'h':
                print("'h' - display help")
                self.display_help()

            else:
                print("Invalid command")
                self.display_help()


if __name__ == '__main__':

    sleep(2)
    
    master = MainMaster()
    master.run()
