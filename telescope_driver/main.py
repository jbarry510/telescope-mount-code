# main.py
# The main code to run on the STM32F411 at the heart of the IMU guide.
#
# Things To Do:
#       Comm with motor driver 1
#       ""  2
#       ""  3
#       Listen to USB bus
#       Run a command


# === THINGS WE PRETEND ARE CONSTANTS ===
__LOOP_DELAY__ = 10 # [us], number of microseconds to wait between main loops

# state aliases
__STATE_INIT__ = 0
__STATE_WAIT__ = 1


# === GLOBAL VARIABLES ===


# === FUNCTIONS AND CLASSES ===
def load_config_data ():
    """ Loads config data from the uSD card for the motors.
    """
    pass # TODO
# /load_config_data

class MotorTask:
    """ The task class for motor drivers.
    """
    def __init__(self, driver_obj):
        self.driver = driver_obj
        self.state = __STATE_INIT__
    
    def run_task (self, cmd_code='init'):
        if self.state == __STATE_INIT__:
            self.driver.GetStatus() # toss the first reading on startup
            if self.driver.GetStatus() != 32275: # init OK status
                # something went wrong, report it and don't activate the motor.
                self.state = __STATE_INIT__
                return
            else:
                # apply configuration data to driver
                #...
                # brake just in case
                self.driver.SoftHiZ()
                self.state = __STATE_WAIT__
        
        # --state: waiting for command--
        elif self.state == __STATE_WAIT__:
            # check the cmd_code to see what to do
            pass
        # --state: unknown--
        else:
            # unknown state somehow?! Brake and go back to waiting.
            print('Unknown state in task_altitude, stopping motor!')
            self.driver.SoftHiZ()
            self.state = __STATE_WAIT__
    # /run_task
# /task_motor

def main ():
    """ The main logic for the script as a program.
        Handles importing modules and initializing global vars.
    """
    # modules we'll be using.
    from pyb import Pin
    from pyb import udelay
    import stmspi
    from L6470_driver import L6470
    
    # create the motor driver objects.
    task_altitude = MotorTask(L6470(stmspi.SPIDevice(2,Pin.cpu.B0 )))
    task_azimuth  = MotorTask(L6470(stmspi.SPIDevice(2,Pin.cpu.B1 )))
    task_focuser  = MotorTask(L6470(stmspi.SPIDevice(2,Pin.cpu.A15)))
    
    # load configuration data from the uSD card.
    load_config_data();
    
    # initialize USB link
    #...
    
    # wait for incoming commands
    cmd_alt = 'init'
    cmd_azi = 'init'
    cmd_foc = 'init'
    
    while (True):
        # call tasks based on the commands
        task_altitude.run_task(cmd_alt)
        #task_azimuth.run_task(cmd_azi)
        #task_focuser.run_task(cmd_foc)
        
        # check for USB data and set new commands
        #...
        udelay(__LOOP_DELAY__)
# /main

# entry point for the program:
if __name__ == "__main__":
    main()
