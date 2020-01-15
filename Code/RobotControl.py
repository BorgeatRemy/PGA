import socket
import math
import binascii
import struct
import math
import array
import RPi.GPIO as GPIO
## @package RobotControl
# control the robot

PLIER_OUT_1 = 11  # pin  of Raspberry connected to plier output1, tightening output
PLIER_OUT_2 = 13  # pin  of Raspberry connected to plier output2, loossing output
PLIER_IN_1 = 16  # pin  of Raspberry connected to plier digital input

#Led assignement
LED_START = 36      #Green led to show when the robot run
LED_STOP = 40       #Red led to show when the robot is stopped
LED_IN_MASTER = 31
LED_GOT_OBJECT = 33

#define
Y_MIN_SEARCH = -0.399
Y_MAX_SEARCH = -0.100
DX_SEARCH = 0.050
DY_SEARCH = 0.050

#Definition of evenement for state Machine
EV_INIT = 0
EV_FOUND = 1
EV_SIX = 2
EV_IN_POS = 3
EV_DOWN = 4
EV_GRAB = 5
EV_UP = 6
EV_RELEASE = 7
EV_POS_Z = 8
EV_NOT_FOUND = 9
EV_IN_POS_OBJECT = 10

#Definition of state for state Machine
ST_INIT = 0
ST_BEGIN_SEARCH = 1
ST_END_SEARCH = 2
ST_GOXY = 3
ST_DOWN = 4
ST_GRAB = 5
ST_UP = 6
ST_THROW = 7
ST_RELEASE = 8

#distance between the camera and the pliers
CAMERA_DISTANCE = 0.05

#define precision of the robotics arm
PRECISION_XYZ = 0.001  #precision of the Tool Center Point in X,Y,Z at 1mm
PRECISION_ANGLE = 0.05 #precision of the Tool Center Point in rz  at 0.05rad

##Control the robot
class RobotControl():
    ##constructor
    def __init__(self):
        ##angular velocity of the robot
        self.angularvelocity = 1
        ##angular acceleration of the robot
        self.angularacceleration = 1
        ##linear velocity of the robot
        self.linearvelocity = 1
        ##linear acceleration of the robot
        self.linearacceleration = 1

        ## tool center point position x
        self.posx = 0
        ## tool center point position y
        self.posy = 0
        ## tool center point position z
        self.posz = 0
        ## tool center point orientation rx
        self.rx = 0
        ## tool center point orientation ry
        self.ry = 0
        ## tool center point orientation rz
        self.rz = 0

        ##x postion of the object to catch
        self.object_posX = 0
        ## y postion of the object to catch
        self.object_posY = 0
        #3 orientation of the object to catch
        self.object_Rz = 0

        #Pliers is opening or closing
        self.takeOrRelease = False

        ##
        self.ZeroReached = -0.555
        ##
        self.MaxReached = -0.555
        ##
        self.evZone = 1
        ##
        self.lastZone = 1
        ##
        self.BorderReached = 0

        ##position x to search the object
        self.xSearch = 0
        ##position y to search the object
        self.ySearch = -0.3
        ##position z to search the object
        self.zSearch = 0.2

        #GPIO Setup input/Output
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        GPIO.setup(PLIER_IN_1, GPIO.OUT)
        GPIO.setup(PLIER_OUT_1, GPIO.IN)
        GPIO.setup(PLIER_OUT_2, GPIO.IN)
        GPIO.setup(LED_IN_MASTER, GPIO.OUT)
        GPIO.setup(LED_GOT_OBJECT, GPIO.OUT)
        GPIO.setup(LED_STOP, GPIO.OUT)
        # initial state of pins
        GPIO.output(LED_IN_MASTER, GPIO.LOW)
        GPIO.output(LED_GOT_OBJECT, GPIO.LOW)
        GPIO.output(LED_STOP, GPIO.LOW)

        ## IP Address of the robot
        self.host = "192.168.1.3"

        ##state of the state machine
        self.state = ST_INIT
        ##oldstate of the state machine
        self.oldState = ST_INIT

        ##camera object
        self.theCamera = None

    ## get camera object
    #  @param self The object pointer.
    #  @param theCamera the camera object.
    def initRelations(self,theCamera):
        self.theCamera = theCamera

    ## Put the robot in original state
    #  @param self The object pointer.
    def calibrate(self):
        HOST = self.host
        PORT = 30002
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        a = "movej([" + str(math.pi / 2) + "," + str(-math.pi / 2) + "," + \
            str(math.pi / 2) + "," + str(-math.pi / 2) + "," + \
            str(-math.pi / 2) + "," + str(0) + "]," + "a=" + \
            str(self.angularacceleration) + ", v=" + str(self.angularvelocity) + ")" + "\n"
        s.send(a.encode())
        s.close()
    ## update robot position
    #  get position X,Y,Z and orientation of tool center point
    #  @param self The object pointer.
    def updateCurrentPosition(self):
        HOST = self.host
        PORT = 30003
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((HOST, PORT))
            #data not used
            packet_not_used = s.recv(4)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(8)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(48)
            packet_not_used = s.recv(48)

            # Current position of the tool center point
            packet_posX = s.recv(8)
            self.posx = struct.unpack('!d', packet_posX)[0]

            packet_posY = s.recv(8)
            self.posy = struct.unpack('!d',packet_posY)[0]

            packet_posZ = s.recv(8)
            self.posz = struct.unpack('!d',packet_posZ)[0]

            packet_rx = s.recv(8)
            self.posx = struct.unpack('!d', packet_rx)[0]

            packet_ry = s.recv(8)
            self.posy = struct.unpack('!d',packet_ry)[0]

            packet_rz = s.recv(8)
            self.posz = struct.unpack('!d',packet_rz)[0]

            s.close()

            #check if we reached the object position, precision of 1mm
            if self.object_posX - PRECISION_MOUVEMENT <= self.posx <=self.object_posX + PRECISION_MOUVEMENT:
                if self.object_posY - PRECISION_MOUVEMENT <= self.posy <= self.object_posY + PRECISION_MOUVEMENT:
                    if self.object_Rz - PRECISION_ANGLE <= self.rz <= self.object_Rz + PRECISION_ANGLE:
                        #generate an event if we reached the desired X,Y position and the correct rz angle
                        self.master(EV_IN_POS_OBJECT)
                        if self.object_posZ- PRECISION_MOUVEMENT <= self.posz <=self.object_posZ + PRECISION_MOUVEMENT:
                            # generate an event if we reached the desired X,Y,Z position and the correct rz angle
                            self.master(EV_POS_Z)

            # check if we reached the research position, precision of 1mm
            if self.xSearch - PRECISION_MOUVEMENT <= self.posx <=self.xSearch + PRECISION_MOUVEMENT:
                if self.ySearch - PRECISION_MOUVEMENT <= self.posy <= self.ySearch + PRECISION_MOUVEMENT:
                    #Generate and event if we reached the desired X,Y position
                    self.master(EV_IN_POS)

        except socket.error as socketerror:
            print("Error: ", socketerror)

#-----------------------------------------------------------------------------------------------------------------------
    ## move the robot to a position XYZ with angle rz
    #  @param x : Position X of the Tool Center Point
    #  @param y : Position Y of the Tool Center Point
    #  @param z : Position Z of the Tool Center Point
    #  @param rz : orientation of the object
    #  @param self The object pointer.
    def moveToPosition(self, x=float, y=float, z=float, rz=float):
        try:
            HOST = self.host
            PORT = 30002

            #create a socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            #connect to Serveur socket seondary of the robot
            s.connect((HOST, PORT))

            # move to position x,y,z
            a = "movel(p[" + str(x) + ", " + str(y) + ", " + str(z) + ", " + \
            str(0) + ", " + str(0) + ", " + str(rz) + "]," + " a=" + \
            str(self.linearacceleration) + ", v=" + str(self.linearvelocity) + ")" + "\n"

            #send data
            s.send(a.encode())
            s.close()
        except Exception:
            print("Error move to setted position")
    ## set the object found postion
    #  @param dx : Delta X of the object from the center of the camera
    #  @param dy : Delta Y of the object from the center of the camera
    #  @param rz : orientation of the object
    #  @param self The object pointer.
    def setObjectPosition(self, dx=float, dy=float, rz=float):
        self.object_posX = self.posx - dx
        self.object_posY = self.posy - CAMERA_DISTANCE - dy
        self.object_Rz = self.rz + rz
    ## check the state of the pliers
    #  @param self The object pointer.
    def statePliers(self):
        #pliers close --> pinceOut1 == 1 and pinceOut2 == 0
        if GPIO.input(PLIER_OUT_1) == 1 and GPIO.input(PLIER_OUT_2) == 0:
            self.master(EV_GRAB)
        # pliers open --> pinceOut1 == 0 and pinceOut2 == 1
        elif GPIO.input(PLIER_OUT_2) == 1 and GPIO.input(PLIER_OUT_1) == 0:
            self.master(EV_RELEASE)
    ## open or close the pliers
    #  @param pliersState True->Open, False->Close
    #  @param self The object pointer.
    def adjustPliers(self, pliersState):
        # if to close the pince
        if (pliersState == False):
            GPIO.output(PLIER_IN_1, GPIO.LOW)  # tighten
        # if to open the pince
        else:
            GPIO.output(PLIER_IN_1, GPIO.HIGH)  # loosen
    ## State machine who manage the soft as follow :
    # Step 1 : Move the pliers
    # Step 2 : Search the dice
    # Step 3 : dice found --> go step 4, else step 1
    # Step 4 : Grab the dice
    # Step 5 : Launch the dice and go back to step 1
    # Stop if the dice is 6
    #  @param self The object pointer.
    #  @param event event to trigger state machine.
    def master(self,event):
        #LED shows this part of the code is executed
        GPIO.output(LED_IN_MASTER, GPIO.HIGH)

        self.oldState = self.state
        # State machine changes
        if self.state == ST_INIT:
            if event==EV_INIT:
                self.state = ST_BEGIN_SEARCH
                print("EV_INIT get")
        elif self.state == ST_BEGIN_SEARCH:
            if event == EV_IN_POS:
                self.state = ST_END_SEARCH
        elif self.state == ST_END_SEARCH:
            if event == EV_SIX:
                win = 1
            elif event == EV_FOUND:
                self.state = ST_GOXY
            elif event == EV_NOT_FOUND:
                self.state = ST_BEGIN_SEARCH
        elif self.state == ST_GOXY:
            if event == EV_IN_POS_OBJECT:
                self.state = ST_DOWN
        elif self.state == ST_DOWN:
            if event == EV_POS_Z:
                self.state = ST_GRAB
        elif self.state == ST_GRAB:
            if event == EV_GRAB:
                self.state = ST_UP
        elif self.state == ST_UP:
            if event == EV_POS_Z:
                self.state = ST_THROW
        elif self.state == ST_THROW:
            if event == EV_RELEASE:
                self.state = ST_BEGIN_SEARCH

        # States operations
        if self.oldState != self.state:
            if self.state == ST_BEGIN_SEARCH:
                print("Begin Search")
                self.takeOrRelease = False
                self.BorderReached = self.xSearch
                # go to zone 1 , zone one is the centeral part of the table
                if self.BorderReached == 0 and self.ySearch == -0.300:
                    self.evZone = 1

                # go to zone 2, zone two is the right part of the table
                if evZone == 1 and self.ySearch == Y_MIN_SEARCH:
                    self.evZone = 2
                # go to zone 3, zone three is the left part of the table
                if self.ZeroReached <= (Y_MIN_SEARCH) and self.BorderReached >= 0.200: #borderReached value is x-direction limit
                    self.evZone = 3

                if self.BorderReached <= -0.200 and self.ZeroReached <= (Y_MIN_SEARCH):
                    self.evZone = 4
                    print("search is complete")

                # Zone 1
                if self.evZone == 1:
                    if self.xSearch == 0 and self.ySearch == -0.200:
                        self.ySearch = Y_MIN_SEARCH
                    else:
                        self.ySearch = -0.200  # attention  not more than this (not less than |-200|)

                # Zone 2
                if self.evZone == 2:
                    # initialize the search in this zone
                    if self.lastZone == 1:
                        self.xSearch = dX
                        self.ySearch = Y_MIN_SEARCH
                        self.MaxReached = Y_MIN_SEARCH
                    # search in positive direction of y
                    if self.MaxReached <= Y_MAX_SEARCH and self.lastZone == self.evZone:
                        self.ySearch = self.ySearch + DY_SEARCH
                        self.MaxReached = self.MaxReached + DY_SEARCH
                        if self.MaxReached > Y_MAX_SEARCH:  # set new value for x
                            self.xSearch = self.xSearch + DX_SEARCH
                            self.ZeroReached = Y_MAX_SEARCH

                    # define new value for y in negative direction
                    if self.ZeroReached >= Y_MIN_SEARCH and self.lastZone == self.evZone:
                        self.ySearch = self.ySearch - DY_SEARCH
                        self.ZeroReached = self.ZeroReached - DY_SEARCH
                        if self.ZeroReached < Y_MIN_SEARCH :  # set new value for x
                            self.xSearch = self.xSearch + DX_SEARCH
                            self.MaxReached = Y_MIN_SEARCH


                # Zone 3
                if self.evZone == 3:
                    # initialize the search in this zone
                    if lastZone == 2:
                        self.xSearch = -DX_SEARCH
                        self.ySearch = Y_MIN_SEARCH
                        self.MaxReached = Y_MIN_SEARCH
                    # search in positive direction of y
                    if self.MaxReached <= Y_MAX_SEARCH and lastZone == evZone:
                        self.ySearch = self.ySearch + DY_SEARCH
                        self.MaxReached = self.MaxReached + DY_SEARCH
                        if self.MaxReached > Y_MAX_SEARCH:  # set new value for x
                            self.xSearch = self.xSearch - DX_SEARCH
                            self.ZeroReached = Y_MAX_SEARCH
                    # define new value for y in negative direction
                    if self.ZeroReached >= Y_MIN_SEARCH and self.lastZone == self.evZone:
                        self.ySearch = self.ySearch - DY_SEARCH
                        self.ZeroReached = self.ZeroReached - DY_SEARCH
                        if self.ZeroReached < Y_MIN_SEARCH:  # set new value for x
                            self.xSearch = self.xSearch - DX_SEARCH
                            self.MaxReached = self.Y_MIN_SEARCH

                self.lastZone = self.evZone
                self.moveToPosition(self.xSearch, self.ySearch, self.zSearch, -1.25)
                # camera : can begin his job, in case finding object call setObject(), in setObject evFound change state
                # if not finding it changes evPass state to authorize go to another point to repeat this process

                # define conditions to move in +y direction
                # define new value for y in positive direction
            elif self.state == ST_END_SEARCH:
                print("End Search")
                self.theCamera.cameraDetectionDice()
            elif self.state == ST_GOXY:
                self.moveToPosition(self.object_posX, self.object_posY, self.posz, self.object_Rz)
            elif self.state == ST_DOWN:
                print("posx,y okay")
                self.object_posZ = 0.05
                self.moveToPosition(self.posx,self.posy,self.object_posZ,self.object_Rz)
            elif self.state == ST_GRAB:
                print("grab")
                self.adjustPince(True)
                self.takeOrRelease = True
            elif self.state == ST_UP:
                self.takeOrRelease = False
                print("go up")
                self.object_posZ = 0.2
                self.moveToPosition(self.posx,self.posy,self.object_posZ,self.rz)
            elif self.state == ST_THROW:
                print("release")
                self.adjustPince(False)
                self.takeOrRelease = True

    ## this function stop the robot and put him in original state
    #  @param self The object pointer.
    def stop(self):
        #stop camera preview
        self.theCamera.camera.stop_preview()
        #init the robot
        self.__init__()
        #put the robot back to origin
        self.calibrate()
        #LED turns off
        GPIO.output(LED_IN_MASTER, GPIO.LOW)
        GPIO.output(LED_START, GPIO.LOW)
        GPIO.output(LED_STOP, GPIO.HIGH)
