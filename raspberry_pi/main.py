# main.py for Raspberry Pi

"""
The main code to run on Raspberry Pi.

Handles:
1.
2.
3.
...
"""

# === IMPORTS ===
import time
import usb.core
import usb.util
from BNO055 import BNO055

# === CONSTANTS ===
__LOOP_DELAY__ = 10  # [us], number of microseconds to wait between loops
__STATE_INIT__ = 0
__STATE_CMD_WAIT__ = 1
__STATE_CALC__ = 2
__STATE_MOVE_WAIT__ = 3
__STATE_IMU_READ__ = 4
__STATE_ERROR__ = 5


# === FUNCTIONS AND CLASSES ===
class Main_Task:

    """
    Main task that the Raspberry Pi portion of the IMU telescope mount.
    """

    def __init__(self):
        """
        Sets initial states and creates task variables
        """
        self._state = __STATE_INIT__
        self.run_task()

    def run_task(self):
        """
        Executes task code for stuff
        """
        if self._state == __STATE_INIT__:

            # Sets up IMU for verifying direction of scope
            # self._imu = BNO055()
            # self._imu.begin()
            # if self._imu.get_calibration_status():
            #     print("IMU is not calibrated, move IMU in a figure 8 motion")
            #     time.sleep(0.5)

            # Connects to stepper motor driver board

            # Find the device
            dev = usb.core.find(idVendor=0xf055, idProduct=0x9800)

            # Was it found?
            if dev is None:
                raise ValueError('Driver board not found')

            # Set active configuration
            dev.set_configuration()
            cfg = dev.get_active_configuration()
            intf = cfg[(0, 0)]

            # Get endpoint instance
            self._ep = usb.util.find_descriptor(
                intf,
                # Match the first OUT endpoint
                custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

            # Checks if endpoint was created
            assert self._ep is not None

        if self._state == __STATE_CMD_WAIT__:
            pass
        if self._state == __STATE_CALC__:
            pass
        if self._state == __STATE_MOVE_WAIT__:
            pass
        if self._state == __STATE_IMU_READ__:
            pass
        if self._state == __STATE_ERROR__:
            pass


if __name__ == '__main__':
    main = Main_Task()
    try:
        # while(True):
        main.run_task()
    except KeyboardInterrupt:
        pass
