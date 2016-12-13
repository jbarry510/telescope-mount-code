## @file L6470_driver.py
#This module implements the command set of the L6470 stepper driver.
#
#    @authors Anthony Lombardi
#    @authors John Barry
#    @date 8 December 2016
#
from math import ceil as math_ceil

## @details This class represents an L6470 stepper driver.
#            Contains representations of all valid commands,
#            as well as dictionaries for the register addresses
#            and the contents of the STATUS register.
#
class L6470:

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
    STATUS_DICT = {} # [    NAME    | OK/DEFAULT VALUE ]
    STATUS_DICT[14] = ['STEP_LOSS_B',1] # stall detection on bridge B
    STATUS_DICT[13] = ['STEP_LOSS_A',1] # stall detection on bridge A
    STATUS_DICT[12] = ['OVERCURRENT',1] # OCD, overcurrent detection
    STATUS_DICT[11] = ['HEAT_SHUTDN',1] # TH_SD, thermal shutdown
    STATUS_DICT[10] = ['HEAT_WARN  ',1] # TH_WN, thermal warning
    STATUS_DICT[ 9] = ['UNDERVOLT  ',1] # UVLO, low drive supply voltage
    STATUS_DICT[ 8] = ['WRONG_CMD  ',0] # Unknown command
    STATUS_DICT[ 7] = ['NOTPERF_CMD',0] # Command can't be performed

    STATUS_DICT[ 3] = ['SWITCH_EDGE',0] # SW_EVN, signals switch falling edge
    STATUS_DICT[ 2] = ['SWITCH_FLAG',0] # switch state. 0=open, 1=grounded

    STATUS_DICT[15] = ['STEPCK_MODE',0] # 1=step-clock mode, 0=normal
    STATUS_DICT[ 4] = ['DIRECTION'  ,1] # 1=forward, 0=reverse
    STATUS_DICT[ 6] = ['MOTOR_STAT' ,0] # two bits: 00=stopped, 01=accel
                                            #           10=decel,   11=const spd
    STATUS_DICT[ 1] = ['BUSY'       ,1] # low during movement commands
    STATUS_DICT[ 0] = ['Hi-Z'       ,1] # 1=hi-Z, 0=motor active

    # === CORE FUNCTIONS ===
    """ Create a new L6470 instance.

           @arg @c spi_handler (obj): reference to the SPI driver this chip will use.

           @returns a new instance of an L6470 object.
    """
    ## @brief  Create a new L6470 object.
    #
    #        @arg @c spi_handler The SPI device to use. Guaranteed to work with stmspi::SPIDevice or stmspi::DummyBus.
    #
    def __init__(self, spi_handler):
        self.spi = spi_handler
        if not hasattr(self.spi,'send_recieve'):
            print ('Invalid SPI object.')
            raise AttributeError

    ## Automatically called when the instance is deleted.
    #                Stops the attached motor as a safety precaution.
    #
    def __del__(self):
        self.HardHiZ() # stop motors ASAP, for safety

    # === L6470 FUNCTION WRAPPERS ===
    ## @brief  No-Operation command. The driver will not react.
    #
    def Nop (self):
        # ze goggles
        self.spi.send_recieve(0,1,0)

    ## @brief  Writes the value <param> to the register named <register>.
    #
    #           @arg @c register (string): A name corresponding to an entry in REGISTER_DICT.
    #           @arg @c value (int): The new value to write to that register.
    #
    def SetParam (self, register, value):
        regdata = L6470.REGISTER_DICT[register]
        send_len = math_ceil(regdata[1]/8)
        self.spi.send_recieve(0b00000000 + regdata[0], 1, 0)
        self.spi.send_recieve(value, send_len, 0)

    ## @brief  Reads the value of the register named <register>.
    #
    #            @arg @c register (string): A name corresponding to an entry in REGISTER_DICT.
    #
    #            @return @c value (byte array): The contents of the selected register.
    #
    def GetParam (self, register):
        regdata = L6470.REGISTER_DICT[register]
        cmd = 0b00100000 + regdata[0]
        send_len = math_ceil(regdata[1]/8)
        recv_len = send_len
        value = self.spi.send_recieve(cmd, send_len, recv_len)
        return value

    ## Sets the target <speed> and <direction>. BUSY flag is low until the
    #                speed target is reached, or the motor hits MAX/MIN_SPEED. Can be
    #                given at any time and runs immediately.
    #
    #            @arg @c speed (int): The target speed. Must be positive.
    #            @arg @c direction (int): Direction to rotate. Must be 1 or 0.
    #
    #            @returns @c -1 if the direction or speed were invalid.
    #            @returns @c  0 if the command ran successfully.
    #
    def Run (self, speed, direction):
        if (direction != 1) and (direction != 0):
            return -1 # invalid argument
        if speed < 0:# or speed > :
            return -1 # invalid argument
        self.spi.send_recieve(0b01010000 + direction,1,0)
        self.spi.send_recieve(speed,3,0)
        return 0

    ## Puts the device into step-clock mode and imposes <direction>. Raises
    #                STEPCK_MODE flag and motor is always considered stopped. Mode
    #                will exit if a constant speed, absolute position, or motion
    #                command are issued. Direction can be changed without exiting
    #                step-clock mode by calling StepClock again with the new
    #                direction. BUSY flag does not go low in this mode, but the
    #                command can only be called when the motor is stopped-
    #                NOTPERF_CMD flag will raise otherwise.
    #
    #            @arg @c direction (int): Direction to rotate. Must be 1 or 0.
    #
    #            @returns @c -1 if the direction argument was invalid.
    #            @returns @c  0 if the command ran successfully.
    #
    def StepClock (self, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        self.spi.send_recieve(0b01011000 + direction,1,0)

    ## Moves a number of microsteps in a given direction. The units of
    #                <steps> are determined by the selected step mode. The BUSY flag
    #                goes low until all steps have happened. This command cannot be
    #                run if the motor is running- NOTPERF_CMD flag will raise
    #                otherwise.
    #
    #            @arg @c steps (int): the number of (micro)steps to perform.
    #            @arg @c direction (int): The direction to rotate. Must be 1 or 0.
    #
    #            @returns @c -1 if the direction argument was invalid.
    #            @returns @c  0 if the command ran successfully.
    #
    def Move (self, steps, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        self.spi.send_recieve(0b01000000 + direction,1,0)
        self.spi.send_recieve(steps,3,0)

    ## Brings motor to the step count of <position> via the minimum path.
    #                The units of <steps> are determined by the selected step mode.
    #                The BUSY flag goes low until the position is reached. This
    #                command can only be run if the motor is stopped- the NOTPERF_
    #                CMD flag will raise otherwise.
    #
    #            @arg @c position (int): the absolute position to rotate to.
    #
    def GoTo (self, position):
        self.spi.send_recieve(0b01100000,1,0)
        self.spi.send_recieve(position,3,0)

    ## Brings motor to the step count of <position>, forcing <direction>.
    #                This command works the same way GoTo() does, but the direction
    #                of rotation is in the direction given by the argument, rather
    #                than the minimum path.
    #
    #            @arg @c position (int): the absolute position to rotate to.
    #            @arg @c direction (int): the direction to rotate in. Must be 1 or 0.
    #
    #            @returns @c -1 if the direction argument was invalid.
    #            @returns @c  0 if the command ran successfully.
    #
    def GoTo_DIR (self, position, direction):
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        cmd = 0b01101000 + direction
        self.spi.send_recieve(cmd,1,0)
        self.spi.send_recieve(position,3,0)

    ## Performs a motion in <direction> at <speed> until Switch is closed,
    #                then performs <action> followed by a SoftStop. If the SW_MODE
    #                bit in the CONFIG register is set low, a HardStop is performed
    #                instead of a SoftStop. This command pulls BUSY low until the
    #                switch-on event occurs. This command can be given anytime and
    #                immediately executes.
    #
    #            @arg @c speed (int): the speed to rotate at. Must be positive.
    #            @arg @c action (int): 0 = reset ABS_POS register, 1 = copy ABS_POS into MARK.
    #            @arg @c direction (int): the direction to rotate in. Must be 1 or 0.
    #
    #            @returns @c -1 if the direction or action argument was invalid.
    #            @returns @c  0 if the command ran successfully.
    #
    def GoUntil (self, speed, action, direction):
        if (action != 1) and (action != 0):
            return -1 # unpermitted behavior
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        self.spi.send_recieve(0b01000010 + (action<<3) + direction,1,0)

    ## Performs a motion in <direction> at minimum speed until Switch is
    #                released (open), then performs <action> followed by a HardStop.
    #                If the minimum speed is less than 5 step/s or low speed
    #                optimization is enabled, the motor turns at 5 step/s. This
    #                command keeps the BUSY flag low until the switch is released and
    #                the motor stops.
    #
    #            @arg @c action (int): 0 = reset ABS_POS register, 1 = copy ABS_POS into MARK.
    #            @arg @c direction (int): the direction to rotate in. Must be 1 or 0.
    #
    #            @returns @c -1 if the direction or action argument was invalid.
    #            @returns @c  0 if the command ran successfully.
    #
    def ReleaseSW (self, action, direction):
        if (action != 1) and (action != 0):
            return -1 # unpermitted behavior
        if (direction != 1) and (direction != 0):
            return -1 # unpermitted behavior
        self.spi.send_recieve(0b01110000 + (action<<3) + direction,1,0)

    ## Brings the motor to the HOME position (ABS_POS == 0) via the shortest
    #                path. Note that this command is equivalent to GoTo(0). If a
    #                direction is mandatory, use GoTo_DIR(). This command keeps the
    #                BUSY flag until the home position is reached. This command can be
    #                given only when the previous command is completed- if BUSY is low
    #                when this command is called, the NOTPERF_CMD flag will raise.
    #
    def GoHome (self):
        self.spi.send_recieve(0b01110000,1,0)

    ## Brings the motor to the MARK position via the minimum path. Note
    #                that this command is equivalent to using GoTo with the value of
    #                the MARK register. Use GoTo_DIR() if a direction is mandatory.
    #
    def GoMark (self):
        self.spi.send_recieve(0b01111000,1,0)

    ## @brief  Resets the ABS_POS register to zero (ie, sets HOME position).
    #
    def ResetPos (self):
        self.spi.send_recieve(0b11011000,1,0)

    ## @brief  Resets the L6470 chip to power-up conditions.
    #
    def ResetDevice (self):
        self.spi.send_recieve(0b11000000,1,0)

    ## Stops the motor, using the value of the DEC register as the
    #                deceleration. When the bridges are in Hi-Z, this command will
    #                exit the Hi-Z state without performing any motion. SoftStop can
    #                be run any time and runs immediately- the BUSY flag will be held
    #                low until the motor stops.
    #
    def SoftStop (self):
        self.spi.send_recieve(0b10110000,1,0)

    ## Stops the motor immediately, with infinite deceleration. This
    #                command interacts with the Hi-Z state and the BUSY flag just
    #                like SoftStop().
    #
    def HardStop (self):
        self.spi.send_recieve(0b10111000,1,0)

    ## Puts bridges into Hi-Z after a deceleration phase using the value of
    #                the DEC register. This command can be run at any time and is
    #                immediately executed, and holds BUSY low until the motor stops.
    #
    def SoftHiZ (self):
        self.spi.send_recieve(0b10100000,1,0)

    ## Puts bridges into hi-z immediately, ignoring the DEC parameter. This
    #                command can be run any time and immediately executes, holding
    #                BUSY low until the motor stops.
    #
    def HardHiZ (self):
        self.spi.send_recieve(0b10101000,1,0)

    ## Returns the value of the STATUS register, and forces the system to
    #                exit from any error state. This command does not reset the Hi-Z
    #                or BUSY flags.
    #
    #            @arg @c verbose (optional int): If this is not zero, the command will print.
    #
    #            @return @c status (int): the two-byte value of the register.
    #
    def GetStatus (self, verbose=0):
        status = self.spi.send_recieve(0b11010000,1,2)
        if verbose:
            self.print_status(status)
        return status

    ## @brief  Formatted printing of status codes for the driver.
    #
    #            @arg @c status (int): the code returned by a GetStatus call.
    #
    def print_status (self, status):
        # === ELSE BEGIN HORROR ===
        # check error flags
        print ("Driver Status: ")#, bin(status))
        for bit_addr in range(7,15):
            print("  Flag ", self.STATUS_DICT[bit_addr][0], ": ", end=="")
            # we shift a 1 to the bit address, then shift the result down again
            if ((status & 1<<bit_addr)>>bit_addr)==self.STATUS_DICT[bit_addr][1]:
                # the result should either be a 1 or 0. Which is 'ok' depends.
                print("ok")
            else:
                print("Alert!")

        # check SCK_MOD
        if status & (1<<15):
            print("  Step-clock mode is on.")
        else:
            print("  Step-clock mode is off.")

        # check MOT_STATUS
        if status & (1<<6):
            if status & (1<<5):
                print("  Motor is at constant speed.")
            else:
                print("  Motor is decelerating.")
        else:
            if status & (1<<5):
                print("  Motor is accelerating.")
            else:
                print("  Motor is stopped.")
        # check DIR
        if status & (1<<4):
            print("  Motor direction is set to forward.")
        else:
            print("  Motor direction is set to reverse.")
        # check BUSY
        if not (status & (1<<1)):
            print("  Motor is busy with a movement command.")
        else:
            print("  Motor is ready to recieve movement commands.")
        # check HiZ
        if status & 1:
            print("  Bridges are in high-impedance mode (disabled).")
        else:
            print("  Bridges are in low-impedance mode (active).")

        # check SW_EVEN flag
        if status & (1<<3):
            print("  External switch has been clicked since last check.")
        else:
            print("  External switch has no activity to report.")
        # check SW_F
        if status & (1<<2):
            print("  External switch is closed (grounded).")
        else:
            print("  External switch is open.")

