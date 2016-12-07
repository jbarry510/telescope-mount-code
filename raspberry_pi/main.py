# main.py for Raspberry Pi
"""
The main code to run on Raspberry Pi.
"""

# === IMPORTS ===
import time
import serial
from datetime import datetime as date
from BNO055 import BNO055
try:
    import ephem
except ImportError:
    print("Pyephem not installed must use manual commands")
from kbhit import KBHit

# === CONSTANTS ===
LOOP_DELAY = 0.1  # [sec], number of seconds to wait between loops
# WAIT_DELAY = 5

STATE_INIT = 0
STATE_CMD_WAIT = 1
STATE_CMD_PROCESS = 2
STATE_IMU_READ = 3
STATE_CAL_AZI = 4
STATE_CAL_ALT = 5
STATE_ERROR = 6

NO_ERROR = 0
ERROR_BAD_STATE = 1


# === FUNCTIONS AND CLASSES ===
class Main_Task:
    """
    Main task that the Raspberry Pi portion of the IMU telescope mount.
    """

    def __init__(self):
        """
        Sets initial states and creates task variables
        """
        # Intializes class member variables
        self._state = STATE_INIT
        self._error = NO_ERROR
        self._wait = 0
        self._imu = None
        self._imu_entry = 1
        self._pre_euler_ang = 0
        self._euler_ang = 0
        self._dev = None
        self._obs = None
        self._key_checker = None
        self._alt = 0
        self._azi = 0

    def run_task(self):
        """
        Executes task code running the Raspberry Pi controlled portion of the
        guided telescope mount. The task has a state machine structure.

        States:
        STATE_INIT        - Initializes IMU and connects to stepper driver board
                          via USB
        STATE_CMD_WAIT    - Waits for input commands from the user
        STATE_CMD_PROCESS - Calculates the values needed to executed the user
                          command
        STATE_MOVE_WAIT   - Waits for the stepper driver board to complete any
                          movement commands
        STATE_IMU_READ    - Reads the IMU sensor for verifying 
        STATE_ERROR       - Handles errors and prints out error messages
        """
        if self._state == STATE_INIT:

            # Sets up IMU for verifying direction of scope
            self._imu = BNO055()
            # Checks if IMU object was created
            if self._imu is None:
                raise ValueError('BNO055 IMU not connected')
            self._imu.begin()

            # Connects to stepper motor driver board via serial port
            try:
                self._dev = serial.Serial('/dev/ttyACM0', baudrate=115200)
            except serial.serialutil.SerialException:
                print("Unable to connect to driver board")

            # Prints messages and creates a keypress checker
            print("Initialization done...")
            print("Press any key to start")
            self._key_checker = KBHit()

            # Transistions to next state
            self._state = STATE_CMD_WAIT

        elif self._state == STATE_CMD_WAIT:

            # Waits for a keypress to move on to command entry
            if self._key_checker.kbhit():
                self._state = STATE_CMD_PROCESS

        elif self._state == STATE_CMD_PROCESS:

            # Waits for user to input
            cmd = raw_input("Enter a command: ")
            split_cmd = cmd.split()

            if split_cmd[0] == "cal":
                if split_cmd[1] == "obs":
                    # Creates an observer for computation of altitude and 
                    # azimuth calculation
                    self._obs = ephem.Observer()
                    # lon = raw_input("Enter longitude of current position: ")
                    # lat = raw_input("Enter latitude of current position: ")
                    # elev = raw_input("Enter elevation at current position: ")

                    # Test values
                    lat = '35:16:57.9'       # +N
                    lon = '-120:39:34.6'      # +E
                    elev = 0
                    self._obs.lon = lon
                    self._obs.lat = lat
                    self._obs.elevation = elev
                elif split_cmd[1] == "alt":
                    self._state = STATE_CAL_ALT
                elif split_cmd[1] == "azi":
                    self._state = STATE_CAL_AZI
                else:
                    print("Not a valid calibration")
            elif split_cmd[0] == "goto":
                if split_cmd[1] == "moon":
                    self._obs.date = date.now()
                    moon = ephem.Moon(self._obs)
                    self._alt = float(moon.alt) * 180/ephem.pi
                    self._azi = float(moon.azi) * 180/ephem.pi
                elif split_cmd[1] == "mars":
                    pass
                else:
                    print("Not a valid target")
                self._dev.write('azi:slew' + str(self._azi) + '\r')
                self._dev.write('alt:slew' + str(self._alt) + '\r')
            elif split_cmd[0] == "test":
                self._dev.write(split_cmd[1] + '\r')
            else:
                print("Not a valid command entry")

        elif self._state == STATE_IMU_READ:
            if self._imu_entry == 1:
                self._euler_ang = self._imu.read_euler()
                self._imu_entry = 0
            else:
                self._pre_euler_ang = self._euler_ang
                self._euler_ang = self._imu.read_euler()

                if abs(self._euler_ang - self._pre_euler_ang) < [1, 1, 1]:
                    self._imu_entry = 1
                    self._state = STATE_CMD_WAIT

        elif self._state == STATE_ERROR:

            if self._error == NO_ERROR:
                self._state = STATE_INIT

            elif self._error == ERROR_BAD_STATE:
                print("Error: Unknown state reached, resetting device")
                self._error = NO_ERROR
        else:
            self._state == STATE_ERROR
            self._error == ERROR_BAD_STATE

if __name__ == '__main__':
    main = Main_Task()
    try:
        while(True):
            main.run_task()
            time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
        pass
