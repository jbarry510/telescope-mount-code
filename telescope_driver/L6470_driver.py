# Python module for L6470 stepper driver board interface.

""" This module implements the command set of the L6470 stepper driver.

Example:
    ...

Attributes:
    ...


"""
class L6470:
    """ This class represents an L6470 stepper driver.
    """
    
    REGISTER_DICT = {} # Register Table:   DESCRIPTION   | xRESET | BIT LEN | ?
    REGISTER_DICT['ABS_POS'   ]= 0x01 # current position | 000000 |   22    | S
    REGISTER_DICT['EL_POS'    ]= 0x02 # Electrical pos   |    000 |    9    | S
    REGISTER_DICT['MARK'      ]= 0x03 # mark position    | 000000 |   22    | W
    REGISTER_DICT['SPEED'     ]= 0x04 # current speed    |  00000 |   20    | 
    REGISTER_DICT['ACC'       ]= 0x05 # accel limit      |    08A |   12    | W
    REGISTER_DICT['DEC'       ]= 0x06 # decel limit      |    08A |   12    | W
    REGISTER_DICT['MAX_SPEED' ]= 0x07 # maximum speed    |    041 |   10    | W
    REGISTER_DICT['MIN_SPEED' ]= 0x08 # minimum speed    |      0 |   13    | S
    REGISTER_DICT['FS_SPD'    ]= 0x15 # full-step speed  |    027 |   10    | W
    REGISTER_DICT['KVAL_HOLD' ]= 0x09 # holding Kval     |     29 |    8    | W
    REGISTER_DICT['KVAL_RUN'  ]= 0x0A # const speed Kval |     29 |    8    | W
    REGISTER_DICT['KVAL_ACC'  ]= 0x0B # accel start Kval |     29 |    8    | W
    REGISTER_DICT['KVAL_DEC'  ]= 0x0C # decel start Kval |     29 |    8    | W
    REGISTER_DICT['INT_SPEED' ]= 0x0D # intersect speed  |   0408 |   14    | H
    REGISTER_DICT['ST_SLP'    ]= 0x0E # start slope      |     19 |    8    | H
    REGISTER_DICT['FN_SLP_ACC']= 0x0F # accel end slope  |     29 |    8    | H
    REGISTER_DICT['FN_SLP_DEC']= 0x10 # decel end slope  |     29 |    8    | H
    REGISTER_DICT['K_THERM'   ]= 0x11 # therm comp factr |      0 |    4    | H
    REGISTER_DICT['ADC_OUT'   ]= 0x12 # ADC output       |     XX |    5    | 
    REGISTER_DICT['OCD_TH'    ]= 0x13 # OCD threshold    |      8 |    4    | W
    REGISTER_DICT['STALL_TH'  ]= 0x14 # STALL threshold  |     40 |    7    | W
    REGISTER_DICT['STEP_MODE' ]= 0x16 # Step mode        |      7 |    8    | H
    REGISTER_DICT['ALARM_EN'  ]= 0x17 # Alarm enable     |     FF |    8    | S
    REGISTER_DICT['CONFIG'    ]= 0x18 # IC configuration |   2E88 |   16    | H
    REGISTER_DICT['STATUS'    ]= 0x19 # Status           |   XXXX |   16    |
    REGISTER_DICT['RESERVED A']= 0x1A # RESERVED         |        |         | X
    REGISTER_DICT['RESERVED B']= 0x1B # RESERVED         |        |         | X
    # ? (Remarks): X = unreadable, W = Writable (always), 
    #              S = Writable (when stopped), H = Writable (when Hi-Z)
    
    
    def __init__(self, name):
        # do init stuff and create personal vars
        self.name = name
    
    #def __del__(self):
        # stuff to do when this instance is being deleted
    
    def test_function(self):
        print ("test passed.")
    
    """ No-Operation command. Does nothing.
    """
    def NOP (self):
        # ze goggles
        # should send (0b00000000)
    
    """ Writes the value <param> to the register named <register>
    """
    def SetParam (self, register, param):
        address = REGISTER_DICT[register]
        # should send (0 & address), then (param)
    
    """ Reads the value of the register named <register>
    """
    def GetParam (self, register):
        address = REGISTER_DICT[register]
        # should send (0b00100000 & address)
        # return some_value
    
    """ Sets the target <speed> and <direction>
    """
    def Run (self, speed, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01010000 & direction), then (speed)
    
    """ Puts the device into step-clock mode and imposes <direction>
    """
    def StepClock (self, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01011000 & direction)
    
    """ Makes <steps> in <direction>, will throw an error if motor is running
    """
    def Move (self, steps, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01000000 & direction), then (steps)
    
    """ Brings motor to the step count of <position> via the minimum path
    """
    def GoTo (self, position):
        # should send (0b01100000), then (position)
    
    """ Brings motor to the step count of <position>, forcing <direction>
    """
    def GoTo_DIR (self, position, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b01101000 & direction), then (position)
    
    """ Performs a motion in <direction> at <speed> until Switch is closed,
            then performs <action> followed by a SoftStop
    """
    def GoUntil (self, speed, action, direction):
        if (action != 1) and (action != 0):
            return -1 # unpermitted behavior
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b10000010 & action & direction) (action is 0b0000X000)
    
    """ Performs a motion in <direction> at minimum speed until Switch is
            released (open), then performs <action> followed by a HardStop
    """
    def ReleaseSW (self, action, direction):
        if (action != 1) and (action != 0):
            return -1 # unpermitted behavior
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        # should send (0b10010010 & action & direction) (action is 0b0000X000)
    
    """ Brings the motor to the HOME position (ABS_POS == 0)
    """
    def GoHome (self):
        # should send (0b01110000)
    
    """ Brings the motor to the MARK position
    """
    def GoMark (self):
        # should send (0b01111000)
    
    """ Resets the ABS_POS register (ie, sets HOME position)
    """
    def ResetPos (self):
        # should send (0b11011000)
    
    """ Device is reset to power-up conditions
    """
    def ResetDevice (self):
        # should send (0b11000000)
    
    """ Stops motor with a deceleration phase
    """
    def SoftStop (self):
        # should send (0b10110000)
    
    """ Stops motor immediately
    """
    def HardStop (self):
        # should send (0b10111000)
    
    """ Puts bridges into hi-Z after a deceleration phase
    """
    def SoftHiZ (self):
        # should send (0b10100000)
    
    """ Puts bridges into hi-z immediately
    """
    def HardHiZ (self):
        # should send (0b10101000)
    
    """ Returns the value of the STATUS register
    """
    def GetStatus (self):
        # should send (0b11010000)
    

