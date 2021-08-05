from machine import Pin, UART
from utime import sleep

class LIN:
    _uart = None
    _led = Pin(25, Pin.OUT)

    @classmethod
    def _checksum(cls, data):
        if cls == LINMaster:
            received = data
            data = [int(x) for x in received]
        if type(data) != type([1]):
            print("Error: your function should return a list of int's")
            print(data)
            return 1
        elif type(data[0]) != type(1):
            print("Error: your function should return a list of int's")
            print(data)
            return 1
        soma = sum(data)
        res = (soma & 0xFF) + ((soma >> 8) & 0xFF)
        return (~(res) & 0xFF)

class LINMaster(LIN):
    TIMEOUT = 50000

    def __init__(self):
        LINMaster._uart = UART(1, 9600, parity=None, stop=1, bits=8, tx=Pin(8), rx=Pin(9))
        LIN._led.on()

    # Asks data from 'slaveID' node
    # return data if Checksum/CRC OK, otherwise return -1 after three attempts
    def send_header(self, slaveID):

        if slaveID > 59 or slaveID < 2:
            print("Forbidden Operation: attempt to use a reserved ID.")
            return -1

        attempts = 0 # Checksum/CRC: if wrong, retry 3 times, return -1 if fail
        success = False

        while not success and attempts < 3:

            LIN._led.off()
            sleep(0.5)
            print("Sending ID", slaveID)

            parity = 0
            for x in range(6):
                parity = parity + ((slaveID >> x) & 0x01)
            parity = parity % 2
            parity = (parity << 1) & 0x03

            id_byte = (((slaveID & 0x3F) << 2) + parity) & 0xFF


            LINMaster._uart.sendbreak() # send BREAK
            LINMaster._uart.write(bytes([0x55])) # send SYNC (0x55) 
            LINMaster._uart.write(bytes([id_byte])) # send slaveID + parity

            # Ignore echo bytes
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
                print("Timeout achieved for slave", slaveID)
                break

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
                # checks if data received is [\x55]
                if received == bytes([LINMaster._checksum(b'\x55')]):
                    return [85]
                else:
                    print("Error during communication with node", slaveID)
                    attempts += 1
                    continue

            if not received:
                attempts += 1
                continue

            attempts += 1
            success = True

            if LINMaster._checksum(received):
                print("Checksum fail:", received)
                success = False

            LIN._led.on()
            sleep(0.5)

        if not success:
            print("Couldn't communicate with node", slaveID)
            return [-1]

        return [x for x in received[:-1]]

class LINSlave(LIN):
    _id_func_list = {}
    _uart = None

    def __init__(self, id, func):
        if LINSlave._id_func_list.get(str(id)) is None:
            LINSlave._id_func_list[str(id)] = func

            self.id = id
            self.func = func
            print("Node", self.id, "waiting for messages...")

            if len(LINSlave._id_func_list) == 1:
                LINSlave._uart = UART(1, 9600, parity=None, stop=1, bits=8, tx=Pin(8), rx=Pin(9))
                
        else:
            print("ID", id, "already in use, please change its value...")

    def __del__(self):
        print("Node", self.id, "shutting down...")
        LINSlave._id_func_list.pop(str(self.id))
        if len(LINSlave._id_func_list) == 0:
            LINSlave._uart = None

    @classmethod
    def send_response(cls, id):
        data = cls._id_func_list[str(id)]()
        checksum = cls._checksum(data)
        print("ID", id, ">", data, checksum)

        for x in data:
            cls._uart.write(bytes([x]))

        cls._uart.write(bytes([checksum]))

        # Ignore echo bytes received
        for x in data:
            while not cls._uart.any():
                pass
            byte = cls._uart.read(1)

        while not cls._uart.any():
            pass
        byte = cls._uart.read(1)

    @classmethod
    def _send_try_again(cls):
        print("Wrong parity, asking data again")

        data = [123]
        checksum = 0
        print("Sending", data, checksum)

        for x in data:
            cls._uart.write(bytes([x]))
            
        cls._uart.write(bytes([checksum]))

    @classmethod
    def check_request(cls):

        while cls._uart is not None:
            LIN._led.on()
            while not cls._uart.any():
                pass
            LIN._led.off()
            received = b''
            count = 0
            while cls._uart.any() or count < 2:
                if cls._uart.any():
                    byte = cls._uart.read(1)
                    if not (count == 0 and byte == b'\x00'):
                        received = received + byte
                        count = count + 1

            id_instance = cls._check_id(received[1])
            if id_instance == -1: # Wrong parity
                cls._send_try_again()
            elif id_instance != 0: # Right ID
                cls.send_response(id_instance)

    @classmethod
    def _check_id(cls, data):
        target = (data >> 2) & 0x3F

        # Check if class has ID instance
        for id in cls._id_func_list:
            if int(id) == target:

                # Check Parity
                parity = 0
                for i in range(8):
                    parity = parity + ((data >> i) & 0x01)

                if parity % 2:
                    return -1

                return int(id)

        return 0

# MASTER MAIN EXAMPLE
# if __name__ == '__main__':
#     sleep(2)
#     lin = LINMaster()
#     slaveID = 4
#     while True:
#         read = lin.send_header(slaveID)
#         if read[0] != -1:
#             print(slaveID, ":", read)
#         else:
#             print("Failed to get data from slave", slaveID)
#             slaveID = 2
#         sleep(2)


# SLAVE MAIN EXAMPLE
# def myFunc():
#     return [97]

# def myFunc2():
#     return [98]

# if __name__ == '__main__':
#     sleep(2)
#     led = Pin(25, Pin.OUT)
#     led.on()
    
#     slave3 = LINSlave(3, myFunc)
#     slave = LINSlave(2, myFunc2)
#     slave2 = LINSlave(2, myFunc2)

#     LINSlave.check_request()

#     while True:
#         pass
