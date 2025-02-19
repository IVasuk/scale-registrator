from time import sleep

import serial
import re


class BasicScale:
    SERIAL_PORT_PARAMS = {}
    SERVICE_COMMANDS = {}
    INDICATION_COMMANDS = {}
    INDICATION_ALIASES = {}
    INDICATION_START_CH = ''
    INDICATION_STOP_CH = ''
    ANSWER_LENGTH = 0

    def __init__(self, uuid, port, baudrate, sleep_timeout, command_timeout, commands):
        self.uuid = uuid
        self.sleep_timeout = sleep_timeout
        self.commands = commands

        self.dev_serial = serial.Serial()
        self.dev_serial.port = port
        self.dev_serial.baudrate = baudrate
        self.dev_serial.bytesize = self.SERIAL_PORT_PARAMS['bytesize']
        self.dev_serial.parity = self.SERIAL_PORT_PARAMS['parity']
        self.dev_serial.stopbits = self.SERIAL_PORT_PARAMS['stopbits']
        self.dev_serial.timeout = command_timeout
        self.dev_serial.write_timeout = command_timeout
        self.dev_serial.xonxoff = False
        self.dev_serial.rtscts = False
        self.dev_serial.dsrdtr = False

    def check(self, command, answer):
        return True

    def parse(self, answer):
        return answer

    def connect(self):
        self.dev_serial.open()

    def close(self):
        self.dev_serial.close()

    def is_open(self):
        return self.dev_serial.is_open

    def write(self,command):
        return self.dev_serial.write(("%s%s%s"%(self.INDICATION_START_CH,command,self.INDICATION_STOP_CH)).encode())

    def read(self):
        return self.dev_serial.read(self.ANSWER_LENGTH)

    def get(self):
        res = {}

        for command in self.commands:
            self.dev_serial.reset_output_buffer()
            self.dev_serial.reset_input_buffer()

            sleep(self.sleep_timeout)

#            print(f'{self.uuid}: writing {self.INDICATION_ALIASES[command]} ...')
            self.write(self.INDICATION_COMMANDS[self.INDICATION_ALIASES[command]])
#            print(f'{self.uuid}: writing {self.INDICATION_ALIASES[command]} OK')

#            print(f'{self.uuid}: readind data {self.INDICATION_ALIASES[command]} ...')
            answer = self.read()
#            print(f'{self.uuid}: readind data OK {self.INDICATION_ALIASES[command]} ({answer})')

            answer = answer.decode()

            if self.check(self.INDICATION_ALIASES[command],answer):
                res[command] = self.parse(answer)

        return res

class XK3118T1(BasicScale):
    SERIAL_PORT_PARAMS = {'bytesize': 8, 'parity': 'N', 'stopbits': 1}
    SERVICE_COMMANDS = {'ST': '\x45', 'SZ': '\x44'}
    INDICATION_COMMANDS = {'NW': '\x42', 'TW': '\x43', 'GW': '\x41'}
    INDICATION_ALIASES = {'net': 'NW', 'tare': 'TW', 'gross': 'GW'}
    INDICATION_START_CH = '\x02'
    INDICATION_STOP_CH = '\x03'
    ANSWER_LENGTH = 16

    def check(self, command, answer):
        pattern = r"\D%s:(?:-|0)\d{6}\(kg\)\D"%(command)

        return re.fullmatch(pattern, answer)

    def parse(self, answer):
        return int(answer[4:11])
