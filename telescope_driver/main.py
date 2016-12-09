""" @file main.py
The main code to run on the STM32F411 at the heart of the IMU guide.

    @authors Anthony Lombardi
    @authors John Barry
    @date 8 December 2016
"""

# === CONSTANTS ===
_LOOP_DELAY    = const(100) # [us], number of microseconds to wait between main loops
_ERR_FLAG_MASK = const(0b0111111000000000) # bit placement of error flags
_ERR_CMD_MASK  = const(0b0000000110000000) # bit placement of cmd error flags

# state aliases
_STATE_INIT = const(0)
_STATE_IDLE = const(1)
_STATE_BUSY = const(2)
_STATE_ERR  = const(3)

# === FUNCTIONS AND CLASSES ===
# def load_config_data ():
#    """ Loads config data from the uSD card for the motors.
#    """
#    pass # TODO
# /load_config_data

class MotorTask:
    """ The task class for motor drivers.
    """
    def __init__(self, name, driver_obj, step_degrees=1.8, teeth_driver=1, teeth_follower=1):
        """ Create a new MotorTask.

            @arg @c driver_obj     The L6470 instance to control.
            @arg @c step_degrees   The number of steps per degree for the motor.
            @arg @c teeth_driver   The number of teeth on the attached gear.
            @arg @c teeth_follower The number of teeth on the driven gear.
        """
        self._name = name
        self._driver = driver_obj
        self._STPD = step_degrees
        self._N_W = teeth_driver
        self._N_F = teeth_follower
        self._driver.ResetDevice()
        self._driver.GetStatus() # throw the first check away
        self._state = _STATE_INIT
        self._err = 0
    
    def shut_off (self):
        """ Shut down the motor and wait for commands.
        """
        self._driver.SoftHiZ()
        self._state = _STATE_IDLE
        self._err = 0
    
    def set_param (self, param_str, value):
        """ Wrapper for the L6470.SetParam function for the L6470 instance
                being controlled by this MotorTask.

            @arg @c param_str The name of the register to set.
            @arg @c value     The new value for the register.
        """
        self._driver.GetStatus() # clear previous errors
        self._driver.SetParam(param_str, value)
        stat = self._driver.GetStatus()
        if (stat & _ERR_CMD_MASK) or ((stat & _ERR_FLAG_MASK) != _ERR_FLAG_MASK):
            self._driver.GetStatus() # try once more
            self._driver.SetParam(param_str, value)
            stat = self._driver.GetStatus()
            if (stat & _ERR_CMD_MASK) or ((stat & _ERR_FLAG_MASK) != _ERR_FLAG_MASK):
                print('Error setting parameter for',self._name,'driver!')
                print(self._driver.print_status(stat))

    def get_angle (self):
        """ Uses the motor's gear ratio and the step mode to calculate
                the current output position, in degrees.

            @return @c angle The angle of the output shaft, in degrees.
        """
        step_count = self._driver.GetParam('ABS_POS')
        step_mode  = 2.0**(self._driver.GetParam('STEP_MODE') & 7)
        return (1.0*self._N_D/self._N_F) * step_count * self._STPD / step_mode

    def run_task (self, cmd_code='init'):
        """ The state machine for the MotorTask.
                Run this once per loop and update the argument from there.

            The command code can be one of the following:
            @li @c init          (re-)initialize this MotorTask.
            @li @c slew @c #     Go to a position, in absolute degrees.
            @li @c turn @c #     Go to a position, in relative degrees.
            @li @c track         Turn at a constant rate.
            @li @c mark @c [set] Go to the MARK position [set the current position as MARK].
            @li @c home @c [set] Go to the HOME position [set the current position as HOME].
            @li @c stop          Stop the motor, with a holding torque.
            @li @c off           Set the motor driver to Hi-Z (coast) mode.

            @arg @c cmd_code A string that represents the requested instruction.

            @return @c error The error code. @c 0 if no error.
        """
        if self._state == _STATE_INIT:
            stat = self._driver.GetStatus()
            if stat == 0 or stat == 65535:
                print('Cannot connect to',self._name,'- Is motor power on?')
                return
            if (stat & _ERR_CMD_MASK) or ((stat & _ERR_FLAG_MASK) != _ERR_FLAG_MASK): # CMD ERR 0 = OK, FLAG ERR 1 = OK
                print('Init error for',self._name,':',stat,'. Trying again...')
                self._state = _STATE_INIT # something went wrong, report it and don't activate the motor.
            else:
                # brake just in case
                print(self._name,'init finished successfully:',stat)
                self._driver.SoftHiZ()
                self._state = _STATE_IDLE
        
        # --state: waiting for command--
        elif self._state == _STATE_IDLE:
            # check the cmd_code to see what to do
            
            stat = self._driver.GetStatus()
            if (stat & _ERR_CMD_MASK) or ((stat & _ERR_FLAG_MASK) != _ERR_FLAG_MASK):
                self._state = _STATE_ERR
                print('Error in',self._name,'driver:','{0:016b}'.format(stat))
                self._driver.print_status(stat)
                self._err = stat
            # go-to-angle commands
            elif cmd_code.startswith('slew'): # absolute angle
                try:
                    angle = float(cmd_code.replace('slew',''))
                    step_reg = self._driver.GetParam('STEP_MODE')
                    step_mode = 2**(step_reg & 7) # mask the upper bits
                    step_value = int( angle * step_mode * (1.0*_N_F / _N_D) / (_STPD/10.0) )
                except ValueError:
                    print('invalid angle given to',self._name,':',cmd_code.replace('slew',''))
                else:
                    self._driver.SoftStop()
                    pyb.udelay(10)
                    self._driver.GoTo(step_value)
                    #print('going to',angle,'(',step_value,'sc)')
                    self._state = _STATE_BUSY
            
            elif cmd_code.startswith('turn'): # relative angle
                try:
                    angle     = float(cmd_code.replace('turn',''))
                    step_reg  = self._driver.GetParam('STEP_MODE')
                    step_mode = 2**(step_reg & 7)
                    del_steps = angle * step_mode * (1.0*_N_F / _N_D) / ( _STPD/10.0)
                    cur_steps = self._driver.GetParam('ABS_POS')
                except ValueError:
                    print('invalid angle given to',self._name,':',cmd_code.replace('turn',''))
                else:
                    self._driver.SoftStop()
                    pyb.udelay(10)
                    self._driver.GoTo( int(cur_steps + del_steps) )
                    self._state = _STATE_BUSY
                    
            # constant speed command
            elif cmd_code == 'track':
                #print('tracking')
                self._driver.SoftStop()
                pyb.udelay(10)
                self._driver.Run(1000,1)
                self._state = _STATE_BUSY
            # MARK position commands
            elif cmd_code.startswith('mark'):
                if 'set' in cmd_code:
                    self.set_param('MARK',self._driver.GetParam('ABS_POS'))
                else:
                    self._driver.GoMark()
                    self.state = _STATE_BUSY
            # HOME position commands
            elif cmd_code.startswith('home'):
                if 'set' in cmd_code:
                    self._driver.SoftStop()
                    pyb.udelay(10)
                    self.set_param('ABS_POS',0)
                else:
                    self._driver.GoHome()
                    self.state = _STATE_BUSY
            # motor halt command
            elif cmd_code == 'stop':
                self._driver.SoftStop()
            # low-power-draw mode command
            elif cmd_code == 'off':
                self._driver.SoftHiZ()
        
        # --state: error has ocurred--
        elif self._state == _STATE_ERR:
            stat = self._driver.GetStatus()
            if (not (stat & _ERR_CMD_MASK)) and ((stat & _ERR_FLAG_MASK) == _ERR_FLAG_MASK):
                self._state = _STATE_IDLE
                self._err = 0

        # --state: executing command--
        elif self._state == _STATE_BUSY:
            self._err = 2 # just notify that we're busy
            stat = self._driver.GetStatus()
            if stat & 1<<1: # BUSY flag is bit 1
                self._state = _STATE_IDLE # change state to accepting new commands
                self._err = 0 # not busy any longer

        # --state: unknown--
        else:
            # unknown state somehow?! Brake and go back to waiting.
            print('Unknown state for', self._name, ', stopping motor!')
            self._driver.SoftHiZ()
            self._state = _STATE_IDLE

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
    task_azimuth  = MotorTask('azimuth', L6470(stmspi.SPIDevice(2,Pin.cpu.B1 )))
#    task_focuser  = MotorTask('focuser', L6470(stmspi.SPIDevice(1,Pin.cpu.A15)))
    
    print('** Setting motor parameters...')
    task_altitude.set_param('STEP_MODE',5) # sets the step mode to 1/32 uStep
    task_altitude.set_param('MAX_SPEED',0x20) # set the max speed to 1/2 of the default
    task_azimuth.set_param ('STEP_MODE',5)
    task_azimuth.set_param('MAX_SPEED',0x20)
    
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
            status_azi = task_azimuth.run_task(cmd_azi)
        #    status_task_focuser.run_task(cmd_foc)

            # reset the commands to avoid duplicates
            cmd_alt = 'wait'
            cmd_azi = 'wait'
            cmd_foc = 'wait'
            
            # check for USB data and set new commands
            if usb.any():
                char = usb.read(1) # read and parse 1 byte at a time
                if char == b'\b':
                    usb_buf.pop() # delete last character
                elif char == b'\r':
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
            udelay(_LOOP_DELAY)
    except KeyboardInterrupt:
        task_altitude.shut_off()
        task_azimuth.shut_off()
    #    task_focuser.shut_off()
# /main

# entry point for the program:
if __name__ == "__main__":
    #pass
    main()
