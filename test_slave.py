from machine import Pin, UART, PWM
from utime import sleep
from lin import LINSlave
from mfrc522 import MFRC522

class Data:
    def __init__(self):
        self.count = 0
        self.data = [0, 85, 1]

    def get_data(self):
        self.count += 1
        return [self.data[self.count % len(self.data)]]


if __name__ == '__main__':
    sleep(2)
    led = Pin(25, Pin.OUT)
    led.on()
    print("Board: ", uname()[0])

    data = Data()

    def func_slave_2():
        return data.get_data()
    
    slave_rfid  = LINSlave(2, func_slave_2)
    LINSlave.check_request()

    while True:
        pass
