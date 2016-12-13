""" @file main.py
The main code to run on Raspberry Pi. The main code consists of one task that handles the user interface with stepper motor driver board.

    @authors John Barry
    @authors Anthony Lombardi

    @date 6 December 2016
"""

# === IMPORTS ===
import time
import serial
from datetime import datetime as date
from BNO055 import BNO055
try:
    import ephem
    import ephem.stars
except ImportError:
    print("PyEphem not installed, must use manual commands")

# === CONSTANTS ===
LOOP_DELAY = 0.1  # [sec], number of seconds to wait between loops

STATE_INIT      = 1
STATE_CMD       = 2
STATE_CAL_IMU   = 3
STATE_CAL_AZI   = 4
STATE_CAL_ALT   = 5
STATE_ALIGN     = 6
STATE_IMU_WAIT  = 7
STATE_ERROR     = 8

NO_ERROR        = 0
ERROR_BAD_STATE = 1


# === FUNCTIONS AND CLASSES ===
class Main_Task:
    """ @class Main_Task
    Main task for the Raspberry Pi portion of the IMU telescope mount.
    """

    def __init__(self):
        """
        Sets initial states and creates task variables.
        """
        # Intializes class member variables
        self._prev_state = None
        self._state = STATE_INIT
        self._error = NO_ERROR
        self._imu = None
        self._imu_entry = True
        self._pre_euler_ang = 0
        self._euler_ang = 0
        self._dev = None
        self._obs = None
        self._key_checker = None
        self._alt = 0
        self._alt_calibrated = 0
        self._azi = 0
        self._azi_calibrated = 0

    def run_task(self):
        """ @brief Executes task code running the Raspberry Pi controlled portion of the guided telescope mount. The task has a state machine structure.

        States:
        @li STATE_INIT     - Initializes IMU and connects to stepper driver board via USB
        @li STATE_CMD      - Waits for input commands from the user and processes user input
        @li STATE_CAL_IMU  - Prints IMU calibration status and waits until IMU is calibrated before exiting
        @li STATE_CAL_ALT  - Sends command to move to zero altitude and waits until done moving
        @li STATE_CAL_AZI  - Sends command to move to north and waits until done moving
        @li STATE_ALIGN    - Handles overall calibration procedure flow
        @li STATE_IMU_WAIT - Waits for IMU to stop changing values
        @li STATE_ERROR    - Handles errors and prints out error messages
        """
        if self._state == STATE_INIT:

            # Sets up IMU for verifying direction of scope
            self._imu = BNO055(serial_port='/dev/ttyAMA0', rst=18)
            # Checks if IMU object was created
            if self._imu is None:
                raise ValueError('BNO055 IMU not connected')
            self._imu.begin()

            # Connects to stepper motor driver board via serial port
            try:
                self._dev = serial.Serial(port='/dev/ttyACM0', baudrate=115200,
                                          timeout=5)
            except serial.serialutil.SerialException:
                print("Unable to connect to driver board")

            # Transistions to next state
            self._prev_state = STATE_INIT
            self._state = STATE_CMD
            
        # Command processing state
        elif self._state == STATE_CMD:
            # Waits for user to input
            cmd = raw_input("\nEnter a command: ")
            split_cmd = cmd.split()

            if split_cmd[0] == "cal":
                if split_cmd[1] == "obs":
                    # Creates an observer for computation of altitude and 
                    # azimuth calculation
                    self._obs = ephem.Observer()
                    # lon = raw_input("Enter longitude of current position: ")
                    # lat = raw_input("Enter latitude of current position: ")
                    # elev = raw_input("Enter elevation at current position: ")

                    # Test values (SLO)
                    lat = '35:16:57.9'        # +N
                    lon = '-120:39:34.6'      # +E
                    elev = 0

                    self._obs.lon = lon
                    self._obs.lat = lat
                    self._obs.elevation = elev
                elif split_cmd[1] == "imu":
                    if self._imu.get_calibration_status()[0] > 0:
                        print("\nIMU is calibrated")
                    else:
                        print('\nStarting IMU calibration...')
                        self._prev_state = STATE_CMD
                        self._state = STATE_CAL_IMU

                elif split_cmd[1] == "polar":
                    if self._obs is None:
                        print("\nLocation has not been set, run command: cal obs")
                    else:
                        if self._imu.get_calibration_status()[0] > 0:
                            self._prev_state = STATE_CMD
                            self._state = STATE_ALIGN
                        else:
                            print("\nIMU calibration is off, run command: cal imu")
                else:
                    print("\nNot a valid calibration command")
            elif split_cmd[0] == "goto":
                if (self._alt_calibrated and self._azi_calibrated) == 1:
                    if split_cmd[1] == "moon":
                        self._obs.date = date.now()
                        moon = ephem.Moon(self._obs)
                        self._alt = float(moon.alt) * 180/ephem.pi
                        self._azi = float(moon.az) * 180/ephem.pi
                    else:
                        print("\nNot a valid target")
                    self._dev.write('azi:slew' + str(self._azi) + '\r')
                    time.sleep(0.001)
                    self._dev.write('alt:slew' + str(self._alt) + '\r')
                else:
                    print("\nDevice not calibrated, run command: cal polar first")
            elif split_cmd[0] == "test":
                self._dev.write(split_cmd[1] + '\r')
            else:
                print("\nNot a valid command entry")

        # Calibration of IMU
        elif self._state == STATE_CAL_IMU:
            cal = self._imu.get_calibration_status()
            print('\nIMU system calibration status: ' + str(cal[0]))
            print('\nGyro calibration status: ' + str(cal[1]))
            print('\nAccel calibration status: ' + str(cal[2]))
            print('\nMag calibration status: ' + str(cal[3]) + '\n')
            if cal[0] > 0:
                self._prev_state = STATE_CAL_IMU
                self._state = STATE_CMD

        # Calibration of altitude axis
        elif self._state == STATE_CAL_ALT:
            # TODO altitude calibration routine (UPDATE DESCRIPTION):
            #   1. Get current IMU orientation (pitch is key)
            #   2. Get altitude of Polaris (or other target) from Pyephem
            #   3. Slew from IMU to target altitude
            #   4. Confirm with user if heading is correct
            #      A. Yes: Continue to [5]
            #      B. No: Allow manual motion, save resulting correction.
            #   5. send 'alt:home set' to the STM board
            # Calibration done.

            print('\nStarting altitude axis calibration...')
            self._euler_ang = self._imu.read_euler()
            self._dev.write('alt:slew ' + str(-self._euler_ang[1]) + '\r')
            if self._prev_state == STATE_IMU_WAIT:
                self._dev.write('alt:home set\r')
                time.sleep(0.001)
                print('\nAltitude axis calibrated.')
                self._alt_calibrated = 1
                self._prev_state = STATE_CAL_ALT
                self._state = STATE_CAL_AZI
            else:
                self._prev_state = STATE_CAL_ALT
                self._state = STATE_IMU_WAIT

        # Calibration of azimuth axis
        elif self._state == STATE_CAL_AZI:
            # TODO azimuth calibration routine (UPDATE DESCRIPTION):
            #   1. Get current IMU orientation (heading is key)
            #   2. Slew to IMU 0 heading (straight north)
            #   3. Confirm with user if heading is correct
            #      A. Yes: Continue to [4]
            #      B. No: Allow manual motion, save resulting correction.
            #   4. send 'azi:home set' to the STM board
            # Calibration done.

            print('\nStarting azimuth axis calibration...')
            self._euler_ang = self._imu.read_euler()
            self._dev.write('azi:slew' + str(-self._euler_ang[0]) + '\r')
            if self._prev_state == STATE_IMU_WAIT:
                self._dev.write('azi:home set\r')
                time.sleep(0.001)
                print('\nAzimuth axis calibrated.')
                self._azi_calibrated = 1
                self._state = STATE_ALIGN
            else:
                self._prev_state = STATE_CAL_AZI
                self._state = STATE_IMU_WAIT

        # Overall calibration procedure state
        elif self._state == STATE_ALIGN:
            if self._prev_state == STATE_CMD:
                print('\nStarting polar alignment calibration:')
                self._prev_state = STATE_ALIGN
                self._state = STATE_CAL_ALT
            elif self._prev_state == STATE_CAL_AZI:
                self._euler_ang = self._imu.read_euler()
                self._obs.date = date.now()
                polaris = ephem.star("Polaris")
                polaris.compute(self._obs)
                pol_alt = polaris.alt * 180/ephem.pi
                pol_azi = polaris.az * 180/ephem.pi
                print('\nAttempting to slew to Polaris...')
                self._azi = pol_azi - self._euler_ang[0]
                self._alt = pol_alt - self._euler_ang[1]
                self._dev.write('azi:slew' + str(self._azi) + '\r')
                time.sleep(0.001)
                self._dev.write('alt:slew' + str(self._alt) + '\r')
                time.sleep(0.001)
                self._prev_state = STATE_ALIGN
                self._state = STATE_IMU_WAIT
            elif self._prev_state == STATE_IMU_WAIT:
                confirm = raw_input('\nIs this position correct? [y/n]')
                if confirm.lower() == 'n':
                    print('\nPlease enter manual slew adjustments.')
                    align_cmd = raw_input('>')
                    while not (align_cmd == 'done'):
                        self._dev.write(align_cmd + '\r')
                        self._euler_ang = self._imu.read_euler()
                        align_cmd = raw_input('\n>')
                print('\nSaving alignment...')
                self._dev.write('azi:home set\r')
                time.sleep(0.001)
                self._dev.write('alt:home set\r')
                time.sleep(0.001)
                print('\nAlignment finished.')
                self._prev_state = STATE_ALIGN
                self._state = STATE_CMD

        # Waits for IMU data to stop changing (i.e. motors finished moving)
        elif self._state == STATE_IMU_WAIT:
            if self._imu_entry is True:
                self._euler_ang = self._imu.read_euler()
                self._imu_entry = False
            else:
                self._pre_euler_ang = self._euler_ang
                self._euler_ang = self._imu.read_euler()
                if abs((self._euler_ang[0] - self._pre_euler_ang[0]) + (self._euler_ang[1] - self._pre_euler_ang[1]) + (self._euler_ang[2] - self._pre_euler_ang[2]))  < 0.1:
                    self._imu_entry = True
                    self._state = self._prev_state
                    self._prev_state = STATE_IMU_WAIT

        # Error state for errors and stuff
        elif self._state == STATE_ERROR:
            if self._error == NO_ERROR:
                self._state = STATE_INIT
            elif self._error == ERROR_BAD_STATE:
                print("Error: Unknown state reached, resetting device")
                self._error = NO_ERROR

        # Error if in a bad state
        else:
            self._state == STATE_ERROR
            self._error == ERROR_BAD_STATE

# Starts state machine if file is executed
if __name__ == '__main__':
    main = Main_Task()
    try:
        while(True):
            main.run_task()
            time.sleep(LOOP_DELAY)
    except KeyboardInterrupt:
        main._dev.write('azi:off\r')
        main._dev.write('alt:off\r')
