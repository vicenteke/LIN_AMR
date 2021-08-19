from machine import Pin, UART, PWM
from utime import sleep
from lin import LINSlave
from mfrc522 import MFRC522

class ServoSG90:
    OPEN = 0
    CLOSED = 1

    def __init__(self):
        self.vcc = Pin(7, Pin.OUT)
        self.vcc.on()

        self.pwm = PWM(Pin(6))
        self.pwm.freq(50)
        self._status = ServoSG90.OPEN
        self.open()

    def status(self):
        return self._status

    def close(self):
        self.pwm.duty_u16(100)
        sleep(0.5)
        self._status = ServoSG90.CLOSED

    def open(self):
        self.pwm.duty_u16(5000)
        sleep(0.5)
        self._status = ServoSG90.OPEN

class RFID:
    MAX_ATTEMPTS = 3
    def __init__(self):
        self.reader = MFRC522(spi_id=0,sck=2,miso=4,mosi=3,cs=1,rst=0)

    def read(self):
        stat = -1
        attempts = RFID.MAX_ATTEMPTS
        while stat != self.reader.OK or attempts:
            (stat, tag_type) = self.reader.request(self.reader.REQIDL)
            attempts -= 1

            if stat == self.reader.OK:
        
                (stat, uid) = self.reader.SelectTagSN()
            
                if stat == self.reader.OK:
                    return uid
                else:
                    return [0]

        return [0]


class MainSlave():
    def __init__(self):
        self.rfid = RFID()
        self.servo = ServoSG90()

        self.slave_rfid          = LINSlave(2, self.func_slave_2)
        self.slave_servo_open    = LINSlave(3, self.func_slave_3)
        self.slave_servo_close   = LINSlave(4, self.func_slave_4)
        self.slave_servo_status  = LINSlave(5, self.func_slave_5)
    
    def func_slave_2(self):
        return self.rfid.read()

    def func_slave_3(self):
        self.servo.open()
        return [self.servo.status()]

    def func_slave_4(self):
        self.servo.close()
        return [self.servo.status()]

    def func_slave_5(self):
        return [self.servo.status()]
    

    def run(self):
        LINSlave.check_request()

        while True:
            pass


if __name__ == '__main__':
    sleep(2)

    slave = MainSlave()
    slave.run()
