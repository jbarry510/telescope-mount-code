# Python module for an SPI bus on the STM64F4 microcontroller.

""" This module implements an SPI bus in master mode, with chip select lines.
"""

import pyb
from pyb import SPI,Pin

# stores the pins used already, so we don't double up
__cs_pins = []
# references to the buses available to us- a dummy and four real buses
__spi_buses = ['off', 'off', 'off', 'off', 'off']

def init_bus (bus_num, baudrate=4000000, polarity=1, phase=1, firstbit='MSB'):
    """ Turn on an SPI bus or reinitialize it if it was on already.
    Args:
        bus_num (int): Must be 1-4. Selects the SPI bus.
        baudrate (opt int): Speed of transmission. Default is 4000000.
        polarity (opt int): Must be 0 or 1. The idle level for the clock line.
        phase (opt int): Must be 0 or 1. Sample data on the first or second clock
            edge, respectively.
        firstbit (opt int): Use 'LSB' or 'MSB' for least or most significant bit
            first, respectively.
    Returns:
        0  if the bus was successfully (re)initialized.
        -1 if there was an argument error.
    """
    if (bus_num > 4) or (bus_num < 0):
        print ("Invalid SPI bus number. Setup failed.")
        return -1
    if (polarity != 1) and (polarity != 0):
        print ("SPI bus polarity must be 0 or 1. Setup failed.")
        return -1
    if (phase != 1) and (phase != 0):
        print ("SPI bus phase must be 0 or 1. Setup failed.")
        return -1
    if firstbit == 'LSB':
        firstbit = SPI.LSB
    elif firstbit == 'MSB':
        firstbit = SPI.MSB
    else:
        print ("Invalid SPI bus bit order. Use 'LSB' or 'MSB'. Setup failed.")
        return -1
    if bus_num == 0:
        # dummy bus
        __spi_buses[0] = __DummyBus()
    else:
        __spi_buses[bus_num] = SPI(bus_num, SPI.MASTER, baudrate=baudrate,
                polarity=polarity, phase=phase, firstbit=firstbit)
    return 0

class SPIDevice:
    def __init__(self, bus_num, chip_select_pin):
        """ Sets up a device to use one of the SPI buses.
        Args:
            bus_num (int): Must be 0-4. Selects a bus to use, where 0 is a fake
                bus for testing.
            chip_select_pin (obj): The pin on the board to use as chip select.
        """
        if __spi_buses[bus_num] == 'off':
            print ("SPI bus ", bus_num, " was off. Using default setup.")
            init_bus(bus_num) # default initilization if one wasn't done
        if chip_select_pin in __cs_pins:
            print ("Designated CS pin is already set up as a chip select.")
            print ("This device will be on the fake bus.")
            self.bus = 0
        else:
            __cs_pins.append(chip_select_pin)
            self.bus = bus_num
            self.cs = Pin(chip_select_pin, Pin.OUT_PP)
        # done
    
    def send_recieve(self, send, send_len, recieve_len):
        """ A basic function using micropython's send and recieve SPI commands
            with added chip select.
        Args:
            send (int): The integer amount for the command you want to send
            send_len (int): The number of bytes being sent in the command
            recieve_len (int): The number of bytes you want to read
        Returns:
            data (int): The response from the SPI command
        """
    
        # breaks 'send' into bytes using a shift and mask.
        data_bytes = [(send>>8*(send_len-byte-1))&0xff for byte in range(0,send_len)]
        # prepare to fill this
        recv_bytes = []
        
        # send data byte by byte
        for byte in data_bytes:
            self.__send_byte(byte)
            pyb.udelay(1)
        # recieve data byte by byte
        for byte in range(0, recieve_len):
            recv_bytes.append(self.__read_byte())
            pyb.udelay(1)
            #print (recv_bytes[byte])
        
        # convert recieved bytes into a single number
        return_data = 0
        for byte in range(0,recieve_len):
            # shift previous values over to make room
            return_data = return_data << 8
            # add the new byte in
            return_data += recv_bytes[byte]
        return return_data
    
    # sender helper
    def __send_byte (self, byte):
        self.cs.value(0)
        pyb.udelay(1)
        __spi_buses[self.bus].send(byte)
        pyb.udelay(1)
        self.cs.value(1)

    # reciever helper
    def __read_byte (self):
        self.cs.value(0)
        pyb.udelay(1)
        data = __spi_buses[self.bus].recv(1)
        pyb.udelay(1)
        self.cs.value(1)
        return (data[0])

class __DummyBus:
    def send_recieve(self, data, send_len, recv_len):
        print ("faked Send: ", hex(data))
        return recv(recv_len)
    
    def send(self, byte):
        print ("Faked Send: ", format(byte, '02X'))
    
    def recv(self, length):
        print("faked Recieve ", length, " bytes.")
        faux_data = 0*range(0,length)
        return faux_data

