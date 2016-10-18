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

spi = SPI(1, SPI.MASTER, polarity=1, phase=1, firstbit=SPI.MSB)
chip_select = Pin(Pin.cpu.C5, Pin.OUT_PP)

# Initialize chip select high
chip_select.value(1)

def send_recieve(send, recieve, chip_select):
    """ A basic function utilizing micropython's send and recieve SPI commands with added chip
    select.

    Args:
        send (int): The integer amount for the command you want to send
        recieve (int): The number of bytes you want to read
        chip_select (obj): Pin object for the chip select pin on the microcontroller

    Returns:
        data (bytearray): The response from the SPI command
    """

    chip_select.value(0)
    spi.send(send)
    data = spi.recv(recieve)
    chip_select.value(1)

    return data