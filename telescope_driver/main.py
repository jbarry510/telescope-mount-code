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
__LOOP_DELAY__    = const(100) # [us], number of microseconds to wait between main loops
__ERR_FLAG_MASK__ = const(0b0111111000000000) # bit placement of error flags
__ERR_CMD_MASK__  = const(0b0000000110000000) # bit placement of cmd error flags

# motor details
STPD = 1.8 # steps per degree
N_D  = 1   # teeth on driver gear
N_F  = 1   # teeth on follower gear

# state aliases
if True:
	STATE_ERR  = 3
	STATE_BUSY = 2
	STATE_IDLE = 1
	STATE_INIT = 0

# === GLOBAL VARIABLES ===


# === FUNCTIONS AND CLASSES ===
# def load_config_data ():
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
        self._driver.ResetDevice()
        self._driver.GetStatus() # throw the first check away
        self._state = STATE_INIT
        self._err = 0
    
    def shut_off (self):
        self._driver.SoftHiZ()
        self._state = STATE_IDLE
        self._err = 0
    
    def set_param (self, param_str, value):
        self._driver.GetStatus() # clear previous errors
        self._driver.SetParam(param_str, value)
        stat = self._driver.GetStatus()
        if (stat & __ERR_CMD_MASK__) or ((stat & __ERR_FLAG_MASK__) != __ERR_FLAG_MASK__):
            print('Error setting parameter for',self._name,'driver!')
            print(self._driver.print_status(stat))

    def get_angle (self):
        step_count = self._driver.GetParam('ABS_POS')
        step_mode  = 2**(self._driver.GetParam('STEP_MODE') & 7)
        return (1.0*N_D/N_F) * (step_count*STPD/step_mode)

    def run_task (self, cmd_code='init'):
        if self._state == STATE_INIT:
            stat = self._driver.GetStatus()
            if stat == 0 or stat == 65535:
                print('Cannot connect to',self._name,'- Is motor power on?')
                return
            if (stat & __ERR_CMD_MASK__) or ((stat & __ERR_FLAG_MASK__) != __ERR_FLAG_MASK__): # CMD ERR 0 = OK, FLAG ERR 1 = OK
                print('Init error for',self._name,':',stat,'. Trying again...')
                self._state = STATE_INIT # something went wrong, report it and don't activate the motor.
            else:
                # brake just in case
                print(self._name,'init finished successfully:',stat)
                self._driver.SoftHiZ()
                self._state = STATE_IDLE
        
        # --state: waiting for command--
        elif self._state == STATE_IDLE:
            # check the cmd_code to see what to do
            
            stat = self._driver.GetStatus()
            if (stat & __ERR_CMD_MASK__) or ((stat & __ERR_FLAG_MASK__) != __ERR_FLAG_MASK__):
                self._state = __STATE_ERR
                print('Error in',self._name,'driver:','{0:016b}'.format(stat))
                self._driver.print_status(stat)
                self._err = stat

            if cmd_code.startswith('slew'):
                try:
                    angle = float(cmd_code.replace('slew',''))
                    step_reg = self._driver.GetParam('STEP_MODE')
                    step_mode = 2**(step_reg & 7) # mask the upper bits
                    step_value = int( angle * step_mode * (1.0*N_F / N_D) / STPD )
                except ValueError:
                    print('invalid angle given to',self._name,':',cmd_code.replace('slew',''))
                else:
                    self._driver.SoftStop()
                    pyb.udelay(10)
                    self._driver.GoTo(step_value)
                    #print('going to',angle,'(',step_value,'sc)')
                    self._state = STATE_BUSY
            if cmd_code == 'track':
                #print('tracking')
                self._driver.SoftStop()
                pyb.udelay(10)
                self._driver.Run(1000,1)
        
        # --state: error has ocurred--
        elif self._state == STATE_ERR:
            stat = self._driver.GetStatus()
            if (not (stat & __ERR_CMD_MASK__)) and ((stat & __ERR_FLAG_MASK__) == __ERR_FLAG_MASK__):
                self._state = STATE_IDLE
                self._err = 0

        # --state: executing command--
        elif self._state == STATE_BUSY:
            self._err = 2 # just notify that we're busy
            stat = self._driver.GetStatus()
            if stat & 1<<1: # BUSY flag is bit 1
                self._state = STATE_IDLE # change state to accepting new commands
                self._err = 0 # not busy any longer

        # --state: unknown--
        else:
            # unknown state somehow?! Brake and go back to waiting.
            print('Unknown state for', self._name, ', stopping motor!')
            self._driver.SoftHiZ()
            self._state = STATE_IDLE

        return self._err
    # /run_task
# /task_motor

def main ():
    """ The main logic for the script as a program.
        Handles importing modules and initializing global vars.
    """
    # modules we'll be using.
    from pyb import USB_VCP, Pin, delay, udelay
    import stmspi
    from L6470_driver import L6470
    
    print('** PyScope booting...')
    delay(1000)
    print('** Initializing motors...')
    
    # create the motor driver objects.
    task_altitude = MotorTask('altitude',L6470(stmspi.SPIDevice(2,Pin.cpu.B0 )))
#    task_azimuth  = MotorTask('azimuth', L6470(stmspi.SPIDevice(2,Pin.cpu.B1 )))
#    task_focuser  = MotorTask('focuser', L6470(stmspi.SPIDevice(1,Pin.cpu.A15)))
    
    print('** Setting motor parameters...')
    task_altitude.set_param('STEP_MODE',5) # sets the step mode to 1/32 uStep
#    task_azimuth.set_param('STEP_MODE',5)
    
    # load configuration data from the uSD card.
#    load_config_data();
    
    # initialize USB link
    usb = USB_VCP()
    if not usb.isconnected():
        print('usb not connected?!')
    usb_buf = bytearray('>') # incoming text buffer
    
    # init the command code vars
    cmd_alt = 'init'
    cmd_azi = 'init'
    cmd_foc = 'init'
    print('** Ready for commands.')
    try:
        while (True):
            # call tasks based on the commands
            status_alt = task_altitude.run_task(cmd_alt)
        #    status_azi = task_azimuth.run_task(cmd_azi)
        #    status_task_focuser.run_task(cmd_foc)
            
            # check for USB data and set new commands
            if usb.any():
                char = usb.read()
                if char == b'\r':
                    # parse command
                    cmd = (''.join(map(chr,usb_buf)))[1:]
                    if cmd.startswith('alt:'):
                        cmd_alt = cmd[4:]
                    elif cmd.startswith('azi:'):
                        cmd_azi = cmd[4:]
                    elif cmd.startswith('foc:'):
                        cmd_foc = cmd[4:]
                    else:
                        print('Specify a target for the command: "alt:","azi:",or "foc:"')
                    # echo as an ACK and clear the buffer
                    usb_buf.extend(b'\r\n')
                    usb.send(usb_buf)
                    usb_buf = bytearray(b'>')
                else:
                    usb_buf.extend(char)
            udelay(__LOOP_DELAY__)
    except KeyboardInterrupt:
        task_altitude.shut_off()
    #    task_azimuth.shut_off()
    #    task_focuser.shut_off()
# /main

# entry point for the program:
if __name__ == "__main__":
    #pass
    main()