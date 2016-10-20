# SPI test script for L6470 stepper driver board

""" This module tests the SPI communications between the STM32F4 MCU and the L6470 stepper driver

Example:
    ...

Attributes:
    ...


"""

import pyb
from pyb import Pin
from pyb import SPI

spi = SPI(2, SPI.MASTER, baudrate=4000000, polarity=1, phase=1, firstbit=SPI.MSB)
chip_select = Pin(Pin.cpu.E7, Pin.OUT_PP)

# Initialize chip select high
chip_select.value(1)

def send_recieve(send, recieve):
    """ A basic function utilizing micropython's send and recieve SPI commands with added chip
    select.

    Args:
        send (int): The integer amount for the command you want to send
        recieve (int): The number of bytes you want to read
        chip_select (obj): Pin object for the chip select pin on the microcontroller

    Returns:
        data (bytearray): The response from the SPI command
    """

    data_bytes = [(send>> 8*(3-byte))&0xff for byte in range(0,4)]
    recv_bytes = [0,0,0,0]
    
    # send data byte by byte
    for byte in data_bytes:
        __send_byte(byte, chip_select)
        pyb.udelay(1)
    # recieve data byte by byte
    for byte in range(0,recieve):
        recv_bytes[byte] = __read_byte(chip_select)
        pyb.udelay(1)
        #print (recv_bytes[byte])
    
    # convert recieved bytes into a single number
    return_data = 0
    for byte in range(0,recieve):
        print("byte ", byte, "is ", recv_bytes[byte])
        return_data += (list(reversed(recv_bytes))[byte])<<(8*byte)
        print("return data is now ", return_data)
    return return_data

# sender helper
def __send_byte (byte, chipsel):
    chip_select.value(0)
    pyb.udelay(1)
    spi.send(byte)
    pyb.udelay(1)
    chip_select.value(1)

# reciever helper
def __read_byte (chipsel):
    chip_select.value(0)
    pyb.udelay(1)
    data = spi.recv(1)
    pyb.udelay(1)
    chip_select.value(1)
    return (data[0])
