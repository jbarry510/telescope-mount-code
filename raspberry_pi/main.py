# main.py for Raspberry Pi
"""
The main code to run on Raspberry Pi.
"""

# === IMPORTS ===
import time
import serial
# from BNO055 import BNO055
# import ephem
from kbhit import KBHit

# === CONSTANTS ===
LOOP_DELAY = 0.25  # [sec], number of seconds to wait between loops

STATE_INIT = 0
STATE_CMD_WAIT = 1
STATE_CMD_PROCESS = 2
STATE_MOVE_WAIT = 3
STATE_IMU_READ = 4
STATE_ERROR = 5

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
        self._imu = None
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
            # self._imu = BNO055()
            # # Checks if IMU object was created
            # if self._imu is None:
            #     raise ValueError('BNO055 IMU not connected')
            # self._imu.begin()

            # Connects to stepper motor driver board via serial port
            try:
                self._dev = serial.Serial(port='/dev/ttyACM0', baudrate=115200,
                                          timeout = 2)
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
                    lon = raw_input("Enter longitude of current position: ")
                    lat = raw_input("Enter latitude of current position: ")
                    elev = raw_input("Enter elevation at current position: ")
                    self._obs.lon = lon
                    self._obs.lat = lat
                    self._obs.elevation = elev
                elif split_cmd[1] == "alt":
                    pass
                elif split_cmd[1] == "azi":
                    pass
                else:
                    print("Not a valid calibration")
            elif split_cmd[0] == "goto":
                if split_cmd[1] == "moon":
                    moon = ephem.Moon(self._obs)
                    self._alt = moon.alt
                    self._azi = moon.azi
                    self._state = STATE_MOVE_WAIT
                elif split_cmd[1] == "mars":
                    mars = ephem.Mars(self._obs)
                    self._alt = mars.alt
                    self._azi = mars.azi
                    self._state = STATE_MOVE_WAIT
                else:
                    print("Not a valid target")
            elif split_cmd[0] == "test":
                self._dev.write(split_cmd[1] + '\r')
                mes_len = self._dev.in_waiting
                print self._dev.read(mes_len)
            else:
                print("Not a valid command entry")

        elif self._state == STATE_MOVE_WAIT:

            self._state = STATE_IMU_READ

        elif self._state == STATE_IMU_READ:

            euler_ang = self._imu.read_euler()
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
