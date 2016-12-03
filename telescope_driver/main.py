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
__LOOP_DELAY__    = 1000 # [us], number of microseconds to wait between main loops
__ERR_FLAG_MASK__ = 0b0111111000000000 # bit placement of error flags
__ERR_CMD_MASK__  = 0b0000000110000000 # bit placement of cmd error flags

# state aliases
__STATE_INIT__ = 0
__STATE_WAIT__ = 1
__STATE_ERR__  = 2
__STATE_BUSY__ = 3

# === GLOBAL VARIABLES ===


# === FUNCTIONS AND CLASSES ===
#def load_config_data ():
#    """ Loads config data from the uSD card for the motors.
#    """
#    pass # TODO
# /load_config_data

class MotorTask:
    """ The task class for motor drivers.
    """
    def __init__(self, name, driver_obj):
        self._name = name
        self._driver = driver_obj
        self._state = __STATE_INIT__
        self._err = 0

    def shut_off (self):
        self._driver.SoftHiZ()
        self._state = __STATE_WAIT__
        self._err = 0

    def run_task (self, cmd_code='init'):
        if self._state == __STATE_INIT__:
            stat = self._driver.GetStatus()
            if stat == 0 or stat == 65535:
                print('Cannot connect to',self._name,'- Is motor power on?')
                return
            if ((stat & __ERR_CMD_MASK__) or not (stat & __ERR_FLAG_MASK__)) != 0: # CMD ERR 0 = OK, FLAG ERR 1 = OK
                print('Init error for',self._name,':',stat,'. Trying again...')
                self._state = __STATE_INIT__ # something went wrong, report it and don't activate the motor.
            else:
                # apply configuration data to driver
                #...
                # brake just in case
                print(self._name,'init finished successfully:',stat)
                self._driver.SoftHiZ()
                self._state = __STATE_WAIT__
        
        # --state: waiting for command--
        elif self._state == __STATE_WAIT__:
            # check the cmd_code to see what to do
            
            stat = self._driver.GetStatus()
            if ((stat & __ERR_CMD_MASK__) or not (stat & __ERR_FLAG_MASK__)) != 0:
                self._state = __STATE_ERR__
                print('Error in',self._name,'driver:','{0:016b}'.format(stat))
                self._driver.print_status(stat)
                self._err = stat

            if cmd_code.startswith('slew'):
                try:
                    angle = float(cmd_code.replace('slew',''))
                    step_value = int(angle*1) # TODO replace with actual math for angle conversion
                except ValueError:
                    print('invalid angle given to',self._name,':',cmd_code.replace('slew',''))
                else:
                    self._driver.SoftStop()
                    pyb.udelay(10)
                    self._driver.GoTo(step_value)
                    print('going to',angle)
                    self._state = __STATE_BUSY__
            if cmd_code == 'track':
                #print('tracking')
                self._driver.SoftStop()
                pyb.udelay(10)
                self._driver.Run(1000,1)
        
        # --state: error has ocurred--
        elif self._state == __STATE_ERR__:
            stat = self._driver.GetStatus()
            if not (stat & __ERR_CMD_MASK__) and ((stat & __ERR_FLAG_MASK__) == __ERR_FLAG_MASK__):
                self._state = __STATE_WAIT__
                self._err = 0

        # --state: executing command--
        elif self._state == __STATE_BUSY__:
            self._err = 2 # just notify that we're busy
            stat = self._driver.GetStatus()
            if stat & 1<<1: # BUSY flag is bit 1
                self._state = __STATE_WAIT__ # change state to accepting new commands
                self._err = 0 # not busy any longer

        # --state: unknown--
        else:
            # unknown state somehow?! Brake and go back to waiting.
            print('Unknown state for', self._name, ', stopping motor!')
            self._driver.SoftHiZ()
            self._state = __STATE_WAIT__

        return self._err
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

    pyb.delay(1000)
    
    # create the motor driver objects.
    task_altitude = MotorTask('altitude',L6470(stmspi.SPIDevice(2,Pin.cpu.B0 )))
    task_azimuth  = MotorTask('azimuth', L6470(stmspi.SPIDevice(2,Pin.cpu.B1 )))
#    task_focuser  = MotorTask('focuser', L6470(stmspi.SPIDevice(1,Pin.cpu.A15)))
    
    # load configuration data from the uSD card.
#    load_config_data();
    
    # initialize USB link
    #...
    
    # wait for incoming commands
    cmd_alt = 'init'
    cmd_azi = 'init'
#    cmd_foc = 'init'
    
    try:
        while (True):
            # call tasks based on the commands
            status_alt = task_altitude.run_task(cmd_alt)
            status_azi = task_azimuth.run_task(cmd_azi)
        #    status_task_focuser.run_task(cmd_foc)
           
            # state-change test code, TODO delete when real logic is ready:
            # ** \
            if cmd_alt == 'init':
                cmd_alt = 'slew200'
                cmd_azi = 'track'
            else:
                cmd_alt = 'track'
            # **/
            
            # check for USB data and set new commands
            #...
            udelay(__LOOP_DELAY__)
    except KeyboardInterrupt:
        task_altitude.shut_off()
        task_azimuth.shut_off()
    #    task_focuser.shut_off()
# /main

# entry point for the program:
if __name__ == "__main__":
    #pass
    main()
