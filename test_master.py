from machine import Pin, UART
from utime import sleep
from lin import LINMaster
from main_master import MainMaster

import unittest

class TestMaster(unittest.TestCase):
    def setUp(self):
        self.main_master = MainMaster()
        self.lin = self.main_master.lin

    def test_communication(self):
        self.lin = LINMaster()
        result = self.lin.send_header(self.main_master.LIN_SERVO_STATUS)[0]
        print("Status:", result)
        self.assertFalse(result == -1)

    def test_wrong_parity(self):
        self.lin = LINMaster()
        slaveID = self.main_master.LIN_SERVO_STATUS
        parity = 0
        for x in range(6):
            parity = parity + ((slaveID >> x) & 0x01)
        parity = parity % 2
        parity = (parity << 1) & 0x03

        # Sending wrong parity
        parity = parity - 1

        id_byte = (((slaveID & 0x3F) << 2) + parity) & 0xFF

        LINMaster._uart.sendbreak() # send BREAK
        LINMaster._uart.write(bytes([0x55])) # send SYNC (0x55) 
        LINMaster._uart.write(bytes([id_byte])) # send slaveID + parity

        for a in range(2):
            timer = LINMaster.TIMEOUT / 2
            while not LINMaster._uart.any() and timer:
                timer -= 1

            if not timer:
                break
            byte = LINMaster._uart.read(1)

            received = b''
            timer = LINMaster.TIMEOUT
            while not LINMaster._uart.any() and timer:
                timer -= 1

            if not timer:
                self.fail("Timeout achieved for slave", slaveID)

            count = 0
            timer = LINMaster.TIMEOUT
            while LINMaster._uart.any() or (count < 2 and timer):
                if LINMaster._uart.any():
                    timer = LINMaster.TIMEOUT
                    byte = LINMaster._uart.read(1)
                    if count == 0 and byte == bytes([id_byte]):
                        count = -1
                    elif count <= 0 and byte == b'\x55':
                        count = -2
                    else:
                        if count < 0:
                            count = 0
                        received = received + byte
                        count = count + 1

                    # wait next byte
                    wait_next = LINMaster.TIMEOUT / 5
                    while not LINMaster._uart.any() and wait_next:
                        wait_next -= 1
                else:
                    timer -= 1

            if not timer:
                self.fail("Error during communication with node", slaveID)

            # Assert that the checksum is wrong
            self.assertTrue(LINMaster._checksum(received))

    def test_server(self):
        self.main_master = MainMaster()
        read_rfid = self.main_master.ask_rfid()
        count = 20

        while read_rfid != self.main_master.RIGHT_RFID_TAG and count:
            print("Please connect the right RFID")
            count -= 1
            read_rfid = self.main_master.ask_rfid()

        if not count:
            self.fail("Could not get right RFID tag")

        self.assertTrue(self.main_master.ask_close())
        self.assertTrue(self.main_master.ask_open())


if __name__ == '__main__':
    sleep(1.5)
    unittest.main()
