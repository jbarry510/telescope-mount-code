# Python module for L6470 stepper driver board interface.

""" This module implements the command set of the L6470 stepper driver.

Example:
    ...

Attributes:
    ...


"""
class L6470:
    """ This class represents an L6470 stepper driver.
            Contains representations of all valid commands,
            as well as dictionaries for the register addresses
            and the contents of the STATUS register.
    """
    
    # === DICTIONARIES ===
    """ Dictionary of available registers and their addresses.
    """
    REGISTER_DICT = {} #        ADDR | LEN |  DESCRIPTION     | xRESET | Write
    REGISTER_DICT['ABS_POS'   ]=[0x01, 22] # current pos      | 000000 |   S
    REGISTER_DICT['EL_POS'    ]=[0x02,  9] # Electrical pos   |    000 |   S
    REGISTER_DICT['MARK'      ]=[0x03, 22] # mark position    | 000000 |   W
    REGISTER_DICT['SPEED'     ]=[0x04, 20] # current speed    |  00000 |   R
    REGISTER_DICT['ACC'       ]=[0x05, 12] # accel limit      |    08A |   W
    REGISTER_DICT['DEC'       ]=[0x06, 12] # decel limit      |    08A |   W
    REGISTER_DICT['MAX_SPEED' ]=[0x07, 10] # maximum speed    |    041 |   W
    REGISTER_DICT['MIN_SPEED' ]=[0x08, 13] # minimum speed    |      0 |   S
    REGISTER_DICT['FS_SPD'    ]=[0x15, 10] # full-step speed  |    027 |   W
    REGISTER_DICT['KVAL_HOLD' ]=[0x09,  8] # holding Kval     |     29 |   W
    REGISTER_DICT['KVAL_RUN'  ]=[0x0A,  8] # const speed Kval |     29 |   W
    REGISTER_DICT['KVAL_ACC'  ]=[0x0B,  8] # accel start Kval |     29 |   W
    REGISTER_DICT['KVAL_DEC'  ]=[0x0C,  8] # decel start Kval |     29 |   W
    REGISTER_DICT['INT_SPEED' ]=[0x0D, 14] # intersect speed  |   0408 |   H
    REGISTER_DICT['ST_SLP'    ]=[0x0E,  8] # start slope      |     19 |   H
    REGISTER_DICT['FN_SLP_ACC']=[0x0F,  8] # accel end slope  |     29 |   H
    REGISTER_DICT['FN_SLP_DEC']=[0x10,  8] # decel end slope  |     29 |   H
    REGISTER_DICT['K_THERM'   ]=[0x11,  4] # therm comp factr |      0 |   H
    REGISTER_DICT['ADC_OUT'   ]=[0x12,  5] # ADC output       |     XX |
    REGISTER_DICT['OCD_TH'    ]=[0x13,  4] # OCD threshold    |      8 |   W
    REGISTER_DICT['STALL_TH'  ]=[0x14,  7] # STALL threshold  |     40 |   W
    REGISTER_DICT['STEP_MODE' ]=[0x16,  8] # Step mode        |      7 |   H
    REGISTER_DICT['ALARM_EN'  ]=[0x17,  8] # Alarm enable     |     FF |   S
    REGISTER_DICT['CONFIG'    ]=[0x18, 16] # IC configuration |   2E88 |   H
    REGISTER_DICT['STATUS'    ]=[0x19, 16] # Status           |   XXXX |
    REGISTER_DICT['RESERVED A']=[0x1A,  0] # RESERVED         |        |   X
    REGISTER_DICT['RESERVED B']=[0x1B,  0] # RESERVED         |        |   X
    # Write: X = unreadable, W = Writable (always), 
    #        S = Writable (when stopped), H = Writable (when Hi-Z)
    
    """ Dictionary for the STATUS register. Contains all error flags,
            as well as basic motor state information.
    """
    STATUS_DICT = {} #        [BIT ADDR | OK/DEFAULT VALUE]
    STATUS_DICT['STEP_LOSS_B'] = [0x4000,1] # stall detection on bridge B
    STATUS_DICT['STEP_LOSS_A'] = [0x2000,1] # stall detection on bridge A
    STATUS_DICT['OVERCURRENT'] = [0x1000,1] # OCD, overcurrent detection
    STATUS_DICT['HEAT_SHUTDN'] = [0x0800,1] # TH_SD, thermal shutdown
    STATUS_DICT['HEAT_WARN'  ] = [0x0400,1] # TH_WN, thermal warning
    STATUS_DICT['UNDERVOLT'  ] = [0x0200,1] # UVLO, low drive supply voltage
    STATUS_DICT['WRONG_CMD'  ] = [0x0100,0] # Unknown command
    STATUS_DICT['NOTPERF_CMD'] = [0x0080,0] # Command can't be performed
    
    STATUS_DICT['SWITCH_EDGE'] = [0x0008,0] # SW_EVN, signals switch falling edge
    STATUS_DICT['SWITCH_FLAG'] = [0x0004,0] # switch state. 0=open, 1=grounded
    
    STATUS_DICT['STEPCK_MODE'] = [0x8000,0] # 1=step-clock mode, 0=normal
    STATUS_DICT['DIRECTION'  ] = [0x0010,1] # 1=forward, 0=reverse
    STATUS_DICT['MOTOR_STAT' ] = [0x0040,0] # two bits: 00=stopped, 01=accel
                                            #           10=decel,   11=const spd
    STATUS_DICT['BUSY'       ] = [0x0002,1] # low during movement commands
    STATUS_DICT['Hi-Z'       ] = [0x0001,1] # 1=hi-Z, 0=motor active
    
    # === CORE FUNCTIONS ===
    """ Create a new L6470 instance.
        Args:
            spi_handler (obj): reference to the SPI driver this chip will use.
        Returns:
            a new instance of an L6470 object.
    """
    def __init__(self, spi_handler):
        self.spi = spi_handler
        if not hasattr(self.spi,'send_recieve'):
            print ('Invalid SPI object.')
            raise AttributeError
    
    def __del__(self):
        # stuff to do if/when this instance is being deleted
        self.HardHiZ() # stop motors ASAP, for safety
    
    def test_function(self):
        print ("test passed.")
    
    # === L6470 HELPER FUNCTIONS ===
    
    
    # === L6470 FUNCTION WRAPPERS ===
    def Nop (self):
        """ No-Operation command. Does nothing.
        """
        # ze goggles
        self.spi.send_recieve(0,1,0)
    
    def SetParam (self, register, value):
        """ Writes the value <param> to the register named <register>.
        Args:
            register (string): A name corresponding to an entry in REGISTER_DICT.
            value (int): The new value to write to that register.
        """
        regdata = L6470.REGISTER_DICT[register]
        self.spi.send_recieve(0b00000000 + regdata[0], 1, 0)
        self.spi.send_recieve(value, regdata[1], 0)
    
    def GetParam (self, register):
        """ Reads the value of the register named <register>.
        Args:
            register (string): A name corresponding to an entry in REGISTER_DICT.
        Returns:
            value (byte array): The contents of the selected register.
        """
        regdata = L6470.REGISTER_DICT[register]
        cmd = 0b00100000 + regdata[0]
        value = self.spi.send_recieve(cmd, regdata[1], regdata[1])
        return value
    
    def Run (self, speed, direction):
        """ Sets the target <speed> and <direction>. BUSY flag is low until the
                speed target is reached, or the motor hits MAX/MIN_SPEED. Can be
                given at any time and runs immediately.
        Args:
            speed (int): The target speed. Must be positive.
            direction (int): Direction to rotate. Must be 1 or 0.
        Returns:
            -1 if the direction or speed were invalid.
             0 if the command ran successfully.
        """
        if (direction != 1) and (direction != 0):
            return -1 # invalid argument
        if speed < 0:# or speed > :
            return -1 # invalid argument
        cmd = ((0b01010000 + direction)<<8) + speed
        self.spi.send_recieve(cmd,2,0)
        return 0
    
    def StepClock (self, direction):
        """ Puts the device into step-clock mode and imposes <direction>. Raises
                STEPCK_MODE flag and motor is always considered stopped. Mode
                will exit if a constant speed, absolute position, or motion
                command are issued. Direction can be changed without exiting
                step-clock mode by calling StepClock again with the new
                direction. BUSY flag does not go low in this mode, but the
                command can only be called when the motor is stopped-
                NOTPERF_CMD flag will raise otherwise.
        Args:
            direction (int): Direction to rotate. Must be 1 or 0.
        Returns:
            -1 if the direction argument was invalid.   
             0 if the command ran successfully.
        """
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01011000 & direction)
    
    def Move (self, steps, direction):
        """ Moves a number of microsteps in a given direction. The units of
                <steps> are determined by the selected step mode. The BUSY flag
                goes low until all steps have happened. This command cannot be
                run if the motor is running- NOTPERF_CMD flag will raise
                otherwise.
        Args:
            steps (int): the number of (micro)steps to perform.
            direction (int): The direction to rotate. Must be 1 or 0.
        Returns:
            -1 if the direction argument was invalid.   
             0 if the command ran successfully.
        """
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01000000 & direction), then (steps)
    
    def GoTo (self, position):
        """ Brings motor to the step count of <position> via the minimum path.
                The units of <steps> are determined by the selected step mode.
                The BUSY flag goes low until the position is reached. This
                command can only be run if the motor is stopped- the NOTPERF_
                CMD flag will raise otherwise.
        Args:
            position (int): the absolute position to rotate to.
        """
        # should send (0b01100000), then (position)
    
    def GoTo_DIR (self, position, direction):
        """ Brings motor to the step count of <position>, forcing <direction>.
                This command works the same way GoTo() does, but the direction
                of rotation is in the direction given by the argument, rather
                than the minimum path.
        Args:
            position (int): the absolute position to rotate to.
            direction (int): the direction to rotate in. Must be 1 or 0.
        Returns:
            -1 if the direction argument was invalid.   
             0 if the command ran successfully.
        """
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01101000 & direction), then (position)
    
    def GoUntil (self, speed, action, direction):
        """ Performs a motion in <direction> at <speed> until Switch is closed,
                then performs <action> followed by a SoftStop. If the SW_MODE
                bit in the CONFIG register is set low, a HardStop is performed
                instead of a SoftStop. This command pulls BUSY low until the
                switch-on event occurs. This command can be given anytime and
                immediately executes.
        Args:
            speed (int): the speed to rotate at. Must be positive.
            action (int): 0 = reset ABS_POS register, 1 = copy ABS_POS into MARK.
            direction (int): the direction to rotate in. Must be 1 or 0.
        Returns:
            -1 if the direction or action argument was invalid.   
             0 if the command ran successfully.
        """
        if (action != 1) and (action != 0):
            return -1 # unpermitted behavior
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b10000010 & action & direction) (action is 0b0000X000)
    
    def ReleaseSW (self, action, direction):
        """ Performs a motion in <direction> at minimum speed until Switch is
                released (open), then performs <action> followed by a HardStop.
                If the minimum speed is less than 5 step/s or low speed
                optimization is enabled, the motor turns at 5 step/s. This
                command keeps the BUSY flag low until the switch is released and
                the motor stops.
        Args:
            action (int): 0 = reset ABS_POS register, 1 = copy ABS_POS into MARK.
            direction (int): the direction to rotate in. Must be 1 or 0.
        Returns:
            -1 if the direction or action argument was invalid.   
             0 if the command ran successfully.
        """
        if (action != 1) and (action != 0):
            return -1 # unpermitted behavior
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b10010010 & action & direction) (action is 0b0000X000)
    
    def GoHome (self):
        """ Brings the motor to the HOME position (ABS_POS == 0) via the shortest
                path. Note that this command is equivalent to GoTo(0). If a
                direction is mandatory, use GoTo_DIR(). This command keeps the
                BUSY flag until the home position is reached. This command can be
                given only when the previous command is completed- if BUSY is low
                when this command is called, the NOTPERF_CMD flag will raise.
        """
        # should send (0b01110000)
    
    def GoMark (self):
        """ Brings the motor to the MARK position via the minimum path. Note 
                that this command is equivalent to using GoTo with the value of
                the MARK register. Use GoTo_DIR() if a direction is mandatory.
        """
        # should send (0b01111000)
    
    def ResetPos (self):
        """ Resets the ABS_POS register to zero (ie, sets HOME position).
        """
        # should send (0b11011000)
    
    def ResetDevice (self):
        """ Resets the L6470 chip to power-up conditions.
        """
        # should send (0b11000000)
    
    def SoftStop (self):
        """ Stops the motor, using the value of the DEC register as the
                deceleration. When the bridges are in Hi-Z, this command will
                exit the Hi-Z state without performing any motion. SoftStop can
                be run any time and runs immediately- the BUSY flag will be held
                low until the motor stops.
        """
        # should send (0b10110000)
    
    def HardStop (self):
        """ Stops the motor immediately, with infinite deceleration. This 
                command interacts with the Hi-Z state and the BUSY flag just
                like SoftStop().
        """
        # should send (0b10111000)
    
    def SoftHiZ (self):
        """ Puts bridges into Hi-Z after a deceleration phase using the value of
                the DEC register. This command can be run at any time and is
                immediately executed, and holds BUSY low until the motor stops.
        """
        # should send (0b10100000)
    
    def HardHiZ (self):
        """ Puts bridges into hi-z immediately, ignoring the DEC parameter. This
                command can be run any time and immediately executes, holding 
                BUSY low until the motor stops.
        """
        # should send (0b10101000)
    
    def GetStatus (self):
        """ Returns the value of the STATUS register, and forces the system to
                exit from any error state. This command does not reset the Hi-Z
                or BUSY flags.
        Returns:
            status (bytearray): the two-byte value of the register.
        """
        # should send (0b11010000)
        
    

