import RPi.GPIO as GPIO 
import sys
from time import sleep
from abc import ABC, abstractmethod
import math


class BitSegment(ABC):

    def __init__(self, next_segment):
        self.next_segment = next_segment

    
    @abstractmethod
    def generate(self, address, verify):
        pass


class DontCareSegment(BitSegment):

    def __init__(self, count, next_segment):
        super().__init__(next_segment)
        self.count = count

    def expand_bits(self, number, count):
        address = []
        number_count = 0
        while(number_count < count):
            temp = (number >> number_count) & 1
            address.insert(0, temp)
            number_count = number_count+1

        return address

    def generate(self, address, verify):
        local_address = []
        number_count = 0
        number = 0
        loop_total = math.pow(2, self.count)
        while(number_count < loop_total):
            bits = self.expand_bits(number_count, self.count)
            self.next_segment.generate(address + bits, verify)
            number_count = number_count+1
        pass


class DefinedSegment(BitSegment):

    def __init__(self, segment, next_segment):
        super().__init__(next_segment)
        self.segment = segment

    def generate(self, address, verify):
        self.next_segment.generate(address + self.segment, verify)
        pass



class WriteSegment(BitSegment):
    #shift registers 
    LATCH_CLOCK_GPIO = 21
    SHIFT_CLOCK_GPIO = 20 
    SERIAL_IN_GPIO = 16 
    OUTPUT_ENABLED_GPIO = 12
    WRITE_CYCLE_GPIO = 4

    #data
    I0_GPIO = 26
    I1_GPIO = 19
    I2_GPIO = 13
    I3_GPIO = 6
    I4_GPIO = 5
    I5_GPIO = 11
    I6_GPIO = 9
    I7_GPIO = 10

    data_gpio = [
            I7_GPIO,
            I6_GPIO,
            I5_GPIO,
            I4_GPIO,
            I3_GPIO,
            I2_GPIO,
            I1_GPIO,
            I0_GPIO
            ]

    def pulse(gpio_line):
        GPIO.output(gpio_line, GPIO.HIGH)
        GPIO.output(gpio_line, GPIO.LOW)

    def pulse_low_high(gpio_line):
        GPIO.output(gpio_line, GPIO.LOW)
        sleep(.001)
        GPIO.output(gpio_line, GPIO.HIGH)
        sleep(.001)

    def write_address_bit(bit):
        if(bit == 1):
            GPIO.output(WriteSegment.SERIAL_IN_GPIO, GPIO.HIGH)
        elif(bit == 0):
            GPIO.output(WriteSegment.SERIAL_IN_GPIO, GPIO.LOW)

        WriteSegment.pulse(WriteSegment.SHIFT_CLOCK_GPIO)

    def write_address(address):

        for i in reversed(address):
            WriteSegment.write_address_bit(i)

        WriteSegment.pulse(WriteSegment.LATCH_CLOCK_GPIO)

    def set_data(self):
        print(*self.data, sep=", ")
        for i,d in enumerate(self.data):
            if(d == 1):
                GPIO.output(WriteSegment.data_gpio[i], GPIO.HIGH)
            elif(d == 0):
                GPIO.output(WriteSegment.data_gpio[i], GPIO.LOW)
            
        WriteSegment.pulse_low_high(WriteSegment.WRITE_CYCLE_GPIO)

    def read_data(self):
        read_data = []
        for i,d in enumerate(self.data):
            data = GPIO.input(WriteSegment.data_gpio[i])
            read_data.append(data)
            assert self.data[i] == data 
            
        print(*read_data, sep=', ')


    def __init__(self, data):
        super().__init__(None)
        self.data = data

    def generate(self, address, verify):
        
        #pad to 16 lines
        for i in range(16 - len(address)):
            address.insert(0, 0)

        print(*address, sep=", ", end=' ---  ')
        WriteSegment.write_address(address)
        if(verify == False):
            self.set_data()
            print("wrote")
        else:
            self.read_data()
            print("read")


class row: 
    def __init__(self, address, values): 
        self.address = address 
        self.values = values



seven_segment = {
         #  I7  I6  I5  I4  I3  I2  I1  I0
         #  DP  A   B   C   D   E   F   G
        -1:[0,  0,  0,  0,  0,  0,  0,  1   ],
        0:[ 0,  0,  0,  0,  0,  0,  0,  0   ],
        1:[ 0,  0,  1,  1,  0,  0,  0,  0   ],
        2:[ 0,  1,  1,  0,  1,  1,  0,  1   ],
        3:[ 0,  1,  1,  1,  1,  0,  0,  1   ],
        4:[ 0,  0,  1,  1,  0,  0,  1,  1   ],
        5:[ 0,  1,  0,  1,  1,  0,  1,  1   ],
        6:[ 0,  1,  0,  1,  1,  1,  1,  1   ],
        7:[ 0,  1,  1,  1,  0,  0,  0,  0   ],
        8:[ 0,  1,  1,  1,  1,  1,  1,  1   ],
        9:[ 0,  1,  1,  1,  0,  0,  1,  1   ]
    
        }


micro_controller  = [
        #                                                   EEPROM 1                            EEPROM 2                            EEPROM 3
              #     A8  A7  A6  A5  A4  A3  A2  A1  A0      I7  I6  I5  I5  I3  I2  I1  I0      I7  I6  I5  I4  I3  I2  I1  I0      I7  I6  I5  I4  I3  I2  I1  I0  
            #       OP4 OP3 OP2 OP1 C3  C2  C1  ZF  CF      HLT MI  RI  RO  IO  II  AI  AO      BI  BO  SO  SU  DI  CO  CI  CE      CC  FI
            #Fetch
            row([   -1, -1, -1, -1, 0,  0,  0,  -1, -1],[   0,  1,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  1,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   -1, -1, -1, -1, 0,  0,  1,  -1, -1],[   0,  0,  0,  1,  0,  1,  0,  0,      0,  0,  0,  0,  0,  0,  0,  1,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #NOP - 0000
            row([   0,  0,  0,  0,  0,  1,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  0,  0,  0,  0,  1,  1,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
           
            #HLT - 0001
            row([   0,  0,  0,  1,  0,  1,  0,  -1, -1],[   1,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #LDA - 0010
            row([   0,  0,  1,  0,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  0,  1,  0,  0,  1,  1,  -1, -1],[   0,  0,  0,  1,  0,  0,  1,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]), 
            row([   0,  0,  1,  0,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #LDB - 0011
            row([   0,  0,  1,  1,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  0,  1,  1,  0,  1,  1,  -1, -1],[   0,  0,  0,  1,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  0,  1,  1,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #STA - 0100
            row([   0,  1,  0,  0,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  0,  0,  0,  1,  1,  -1, -1],[   0,  0,  1,  0,  0,  0,  0,  1,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  0,  0,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #STB - 0101
            row([   0,  1,  0,  1,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  0,  1,  0,  1,  1,  -1, -1],[   0,  0,  1,  0,  0,  0,  0,  0,      0,  1,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  0,  1,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #ADD - 0110
            row([   0,  1,  1,  0,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  1,  0,  0,  1,  1,  -1, -1],[   0,  0,  0,  1,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  1,  0,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  1,  0,      0,  0,  1,  0,  0,  0,  0,  0,      0,  1,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  1,  0,  1,  0,  1,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #SUB - 0111
            row([   0,  1,  1,  1,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  1,  1,  0,  1,  1,  -1, -1],[   0,  0,  0,  1,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  1,  1,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  1,  0,      0,  0,  1,  1,  0,  0,  0,  0,      0,  1,  0,  0,  0,  0,  0,  0   ]),
            row([   0,  1,  1,  1,  1,  0,  1,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #JMP - 1000
            row([   1,  0,  0,  0,  0,  1,  0,  -1, -1],[   0,  0,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  1,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  0,  0,  0,  0,  1,  1,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #JZ  - 1001
            row([   1,  0,  0,  1,  0,  1,  0,   0, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            row([   1,  0,  0,  1,  0,  1,  0,   1, -1],[   0,  0,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  1,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  0,  0,  1,  0,  1,  1,   1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #JC -  1010
            row([   1,  0,  1,  0,  0,  1,  0,  -1,  0],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            row([   1,  0,  1,  0,  0,  1,  0,  -1,  1],[   0,  0,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  1,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  0,  1,  0,  0,  1,  1,  -1,  1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #DA -  1011
            row([   1,  0,  1,  1,  0,  1,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  1,      0,  0,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  0,  1,  1,  0,  1,  1,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #DB -  1100
            row([   1,  1,  0,  0,  0,  1,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  1,  0,  0,  0,  1,  1,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),

            #DM -  1101
            row([   1,  1,  0,  1,  0,  1,  0,  -1, -1],[   0,  1,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  1,  0,  1,  0,  1,  1,  -1, -1],[   0,  0,  0,  1,  0,  0,  0,  0,      0,  0,  0,  0,  1,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            row([   1,  1,  0,  1,  1,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      1,  0,  0,  0,  0,  0,  0,  0   ]),
            
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),
            #row([   0,  0,  0,  0,  0,  0,  0,  -1, -1],[   0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0,      0,  0,  0,  0,  0,  0,  0,  0   ]),

        
]

def init_control_lines():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(WriteSegment.SERIAL_IN_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.SERIAL_IN_GPIO, GPIO.LOW)

    GPIO.setup(WriteSegment.SHIFT_CLOCK_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.SHIFT_CLOCK_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.LATCH_CLOCK_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.LATCH_CLOCK_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.WRITE_CYCLE_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.WRITE_CYCLE_GPIO, GPIO.HIGH)
    
    GPIO.setup(WriteSegment.OUTPUT_ENABLED_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.OUTPUT_ENABLED_GPIO, GPIO.HIGH)

def init_data_write():
    GPIO.setup(WriteSegment.I0_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I0_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I1_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I1_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I2_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I2_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I3_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I3_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I4_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I4_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I5_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I5_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I6_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I6_GPIO, GPIO.LOW)
    
    GPIO.setup(WriteSegment.I7_GPIO, GPIO.OUT)
    GPIO.output(WriteSegment.I7_GPIO, GPIO.LOW)

def init_data_read():
    GPIO.setup(WriteSegment.I0_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I1_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I2_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I3_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I4_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I5_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I6_GPIO, GPIO.IN)
    GPIO.setup(WriteSegment.I7_GPIO, GPIO.IN)


def build_segments(address, data):
    dont_care_count = -1
    defined = []
    cur = None
    first = None
    for a in address:
        if(a == -1 and len(defined) > 0): #defined -> don't care
            segment = DefinedSegment(defined, None)
            if(cur != None):
                cur.next_segment = segment
            else:
                first = segment
            cur = segment
            defined = []
        elif(a != -1 and dont_care_count != -1): # don't care -> defined
            segment = DontCareSegment(dont_care_count, None)
            if(cur != None):
                cur.next_segment = segment
            else:
                first = segment
            cur = segment
            dont_care_count = -1

        if(a == -1):
            if(dont_care_count == -1):
                dont_care_count = 0
            dont_care_count = dont_care_count + 1

        if(a != -1):
            defined.append(a)

    if(dont_care_count != -1): #last one is don't care
        segment = DontCareSegment(dont_care_count, None)
        
    if(len(defined) > 0): #last one is defined
        segment = DefinedSegment(defined, None)

    if(cur != None):
        cur.next_segment = segment
    else:
        first = segment
    cur = segment
    
    segment = WriteSegment(data)
    cur.next_segment = segment
    return first


def write_controller(eeprom_block):
    start = (eeprom_block - 1) * 8
    end = start+8
    for r in micro_controller:
        data = r.values[slice(start, end)]
        segment = build_segments(r.address, data)
        segment.generate([], False)

def read_controller(eeprom_block):
    start = (eeprom_block - 1) * 8
    end = start+8
    for r in micro_controller:
        data = r.values[slice(start, end)]
        segment = build_segments(r.address, data)
        segment.generate([], True)


def erase_controller():
    segment = DontCareSegment(13, WriteSegment([0,0,0,0,0,0,0,0]))
    segment.generate([], False)


def program_controller(eeprom_block):
    print(f'using eeprom block: {eeprom_block}')    
    init_control_lines()
    init_data_write()

    erase_controller()
    write_controller(eeprom_block)

    #segment = DefinedSegment([1,1,1,1,1,1,1,1], WriteSegment([0,1,1,0,0,1,0,1]))
    #segment.generate([], False)

    GPIO.output(WriteSegment.OUTPUT_ENABLED_GPIO, GPIO.LOW)
    
    init_data_read()
    read_controller(eeprom_block)
    #segment.generate([], True)

def write_seven_segment(verify):
    #unsigned numbers
    for d in range(256):
        ones = d % 10
        hundreds = d // 100
        tens = (d // 10) - (10 * hundreds) 

        address = []
        number_count = 0
        while(number_count < 8):
            temp = (d >> number_count) & 1
            address.insert(0, temp)
            number_count = number_count+1
        

        #00 - ones
        segment = DefinedSegment([0,0,0]+address, WriteSegment(seven_segment[ones]))
        segment.generate([], verify)

        #01 - tens
        segment = DefinedSegment([0,0,1]+address, WriteSegment(seven_segment[tens]))
        segment.generate([], verify)

        #10 - hundreds
        segment = DefinedSegment([0,1,0]+address, WriteSegment(seven_segment[hundreds]))
        segment.generate([], verify)

        #sign. This is off
        segment = DefinedSegment([0,1,1]+address, WriteSegment([0,0,0,0,0,0,0,0]))
        segment.generate([], verify)

        #signed
    for d in range(-128,128,1):
        
        address = []
        number_count = 0
        while(number_count < 8):
            temp = (d >> number_count) & 1
            address.insert(0, temp)
            number_count = number_count+1
        
        if(d < 0):
            address[0] = 1
            d = d * -1

        ones = d % 10
        hundreds = d // 100
        tens = (d // 10) - (10 * hundreds) 
        
        #00 - ones
        segment = DefinedSegment([1,0,0]+address, WriteSegment(seven_segment[ones]))
        segment.generate([], verify)

        #01 - tens
        segment = DefinedSegment([1,0,1]+address, WriteSegment(seven_segment[tens]))
        segment.generate([], verify)

        #10 - hundreds
        segment = DefinedSegment([1,1,0]+address, WriteSegment(seven_segment[hundreds]))
        segment.generate([], verify)

        #sign.
        if(address[0] == 0):
            segment = DefinedSegment([1,1,1]+address, WriteSegment([0,0,0,0,0,0,0,0]))
        else:
            segment = DefinedSegment([1,1,1]+address, WriteSegment(seven_segment[-1]))
        
        segment.generate([], verify)



def program_seven_segment():
    init_control_lines()
    init_data_write()
    erase_controller()
    write_seven_segment(False)
    
    GPIO.output(WriteSegment.OUTPUT_ENABLED_GPIO, GPIO.LOW)
    init_data_read()
    write_seven_segment(True)

def main(args):
    eeprom_block = 1
    if(len(args) > 0):
        eeprom_block = int(args[0])

    program_seven_segment()



if __name__ == "__main__":
    main(sys.argv[1:])

