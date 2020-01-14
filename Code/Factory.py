import socket
import math
import binascii
import struct
import math
import array
import RPi.GPIO as GPIO
global newX, newY, newZ, newRx, newRy, newRz, objX, objY, objZ, binX, binY, binZ, pinceHeight , evFound , evSearch, evPass, evZone,lastZone, BorderReached
pinceHeight =0
xMax=0
xMin=0
yMax=0
yMin=0
zMax=0
zMin=0
object_width_Max=0
object_height_Max=0
object_depth_Max=0
gotObject=0
gotBin=0
xMidPoint=0
yMidPoint=0
zMidPoint =0
ZeroReached=0
MaxReached=0
BorderReached =0
dX = 0.150
dY = 0.133
pinceOut1=0
pinceOut2=0
pinceIn1=0
led_Start=0
led_Stop=0
led_In_Master=0
led_Got_Object=0

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

ST_INIT = 0
ST_BEGIN_SEARCH = 1
ST_END_SEARCH = 2
ST_GOXY = 3
ST_DOWN = 4
ST_GRAB = 5
ST_UP = 6
ST_THROW = 7
ST_RELEASE = 8

state = 0
oldState = 0
event = 0

CAMERA_DISTANCE = 0.05

taken = 0
class RobotControl():
    def __init__(self):
        self.angle = math.pi
        self.angularvelocity = 1
        self.angularacceleration = 1
        self.linearvelocity = 1
        self.linearacceleration = 1
        # Positonsvariablen fur die Achse 0
        self.angle0Rad = 0
        # Positionsvariblen fur die Achse 1
        self.angle1Rad = 0
        # Positionsvariblen fur die Achse 2
        self.angle2Rad = 0
        # Positionsvariblen fur die Achse 3
        self.angle3Rad = 0
        # Positionsvariblen fur die Achse 4
        self.angle4Rad = 0
        # Positionsvariblen fur die Achse 5
        self.angle5Rad = 0
        # TCP
        self.posx = 0
        self.posy = 0
        self.posz = 0

        self.rx = 0
        self.ry = 0
        self.rz = 0


        self.object_posX = -0.011
        self.object_posY = -0.305
        self.object_posZ = 0
        self.object_Rz = 0
        self.object_width = 0
        self.object_height = 0
        self.object_depth = 0

        self.takeOrRelease = False
        # assigne variables:
        global  pinceHeight

        pinceHeight = 0.1


        evFound = False;
        evSearch = True;
        evPass = False
        global xMax, xMin, yMax, yMin, zMax, zMin, object_width_Max, object_height_Max, object_depth_Max, xMidPoint, yMidPoint, zMidPoint
        xMax = 0.610
        yMax = -0.35
        xMin = -0.610
        yMin = -0.540
        zMax = 0.685
        zMin = 0.013
        object_width_Max = 0.008
        object_height_Max =  0.008
        object_depth_Max = 0.008
        xMidPoint = 0
        yMidPoint = -0.250
        zMidPoint = 0.250

        zAve = 300
        dX = 0.15  # a fraction of |xMax|
        dY = 0.133 # a fraction of |yMin|
        dZ = 0.0
        global ZeroReached, MaxReached, BorderReached,evZone, lastZone
        ZeroReached = -0.555
        MaxReached = -0.555
        evZone = 1
        lastZone = 1
        BorderReached = 0

        BorderReached = 0
        self.xSearch = 0
        self.ySearch = -0.3
        self.zSearch = 0.2
        self.rzSearch = 0


        # assigne new variables for managing the pince
        global pinceOut1, pinceOut2, pinceIn1
        pinceOut1 = 11  # pin  of Raspberry connected to plier output1, tightening output
        pinceOut2 = 13  # pin  of Raspberry connected to plier output2, loossing output
        pinceIn1 = 16  # pin  of Raspberry connected to plier digital input
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(pinceIn1, GPIO.OUT)
        GPIO.setup(pinceOut1, GPIO.IN)
        GPIO.setup(pinceOut2, GPIO.IN)

        # assigne pins for LEDs showing which part of the code is used by machine
        global led_Start, led_Stop, led_In_Master, led_Got_Object
        led_Start = 36
        led_Stop  = 40
        led_In_Master = 31
        led_Got_Object = 33

        GPIO.setup(led_In_Master, GPIO.OUT)
        GPIO.setup(led_Got_Object, GPIO.OUT)
        # initial state of pins
        GPIO.output(led_In_Master, GPIO.LOW)
        GPIO.output(led_Got_Object, GPIO.LOW)

        # Netzwerk
        self.host = "192.168.1.3"

        self.state = ST_INIT
        self.oldState = ST_INIT

        self.theCamera = None

# -----------------------------------------------------------------------------------------------------------------------
    def initRelations(self,theCamera):
        self.theCamera = theCamera
#-----------------------------------------------------------------------------------------------------------------------
    def calibrate(self):
        HOST = self.host
        PORT = 30002
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        a = "movej([" + str(self.angle / 2) + "," + str(-self.angle / 2) + "," + \
            str(self.angle / 2) + "," + str(-self.angle / 2) + "," + \
            str(-self.angle / 2) + "," + str(0) + "]," + "a=" + \
            str(self.angularacceleration) + ", v=" + str(self.angularvelocity) + ")" + "\n"
        s.send(a.encode())
        s.close()
#-----------------------------------------------------------------------------------------------------------------------
    def updateCurrentPosition(self):
        HOST = self.host
        PORT = 30003
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((HOST, PORT))
            packet_1 = s.recv(4)
            packet_2 = s.recv(8)
            packet_3 = s.recv(48)
            packet_4 = s.recv(48)
            packet_5 = s.recv(48)
            packet_6 = s.recv(48)
            packet_7 = s.recv(48)

            # Current angle of the axis
            packet_8 = s.recv(8)
            packet_8 = binascii.hexlify(packet_8)  # Conversion to hexadecimal
            self.angle0Rad = struct.unpack('!d', binascii.unhexlify(packet_8))[0]

            packet_9 = s.recv(8)
            packet_9 = binascii.hexlify(packet_9)  # Conversion to hexadecimal
            self.angle1Rad = struct.unpack('!d', binascii.unhexlify(packet_9))[0]

            packet_10 = s.recv(8)
            packet_10 = binascii.hexlify(packet_10)  # Conversion to hexadecimal
            self.angle2Rad = struct.unpack('!d', binascii.unhexlify(packet_10))[0]

            packet_11 = s.recv(8)
            packet_11 = binascii.hexlify(packet_11)  # Conversion to hexadecimal
            self.angle3Rad = struct.unpack('!d', binascii.unhexlify(packet_11))[0]

            packet_12 = s.recv(8)
            packet_12 = binascii.hexlify(packet_12)  # Conversion to hexadecimal
            self.angle4Rad = struct.unpack('!d', binascii.unhexlify(packet_12))[0]

            packet_13 = s.recv(8)
            packet_13 = binascii.hexlify(packet_13)  # Conversion to hexadecimal
            self.angle5Rad = struct.unpack('!d', binascii.unhexlify(packet_13))[0]

            while (self.angle5Rad < 0):
                self.angle5Rad += 2 * math.pi
            while (self.angle5Rad > 2 * math.pi):
                self.angle5Rad -= 2 * math.pi

            packet_13 = s.recv(48)
            packet_14 = s.recv(48)
            packet_15 = s.recv(48)

            # Current position of the axis
            packet_16 = s.recv(8)
            packet_16 = binascii.hexlify(packet_16)  # Conversion to hexadecimal
            self.posx = struct.unpack('!d', binascii.unhexlify(packet_16))[0]

            packet_17 = s.recv(8)
            packet_17 = binascii.hexlify(packet_17)  # Conversion to hexadecimal
            self.posy = struct.unpack('!d', binascii.unhexlify(packet_17))[0]

            packet_18 = s.recv(8)
            packet_18 = binascii.hexlify(packet_18)  # Conversion to hexadecimal
            self.posz = struct.unpack('!d', binascii.unhexlify(packet_18))[0]

            packet_19 = s.recv(8)
            packet_19 = binascii.hexlify(packet_19)  # Conversion to hexadecimal
            self.rx = struct.unpack('!d', binascii.unhexlify(packet_19))[0]

            packet_20 = s.recv(8)
            packet_20 = binascii.hexlify(packet_20)  # Conversion to hexadecimal
            self.ry = struct.unpack('!d', binascii.unhexlify(packet_20))[0]

            packet_21 = s.recv(8)
            packet_21 = binascii.hexlify(packet_21)  # Conversion to hexadecimal
            self.rz = struct.unpack('!d', binascii.unhexlify(packet_21))[0]
            s.close()
            if (self.posx < (self.object_posX + 0.01) and self.posx > (self.object_posX - 0.01) ):
                if(self.posy < (self.object_posY + 0.01) and self.posy > (self.object_posY - 0.01)):
                    if(self.rz < (self.object_Rz + 0.05) and self.rz > (self.object_Rz - 0.05)):
                        self.master(EV_IN_POS_OBJECT)
                        if (self.posz < (self.object_posZ + 0.001) and self.posz > (self.object_posZ - 0.001)):
                            self.master(EV_POS_Z)
            if (self.posx < (self.xSearch + 0.01) and self.posx > (self.xSearch - 0.01)):
                if(self.posy < (self.ySearch + 0.01) and self.posy > (self.ySearch - 0.01)):
                    self.master(EV_IN_POS)
        except socket.error as socketerror:
            print("Error: ", socketerror)

#-----------------------------------------------------------------------------------------------------------------------
        # move the robot to a position x,y,z :
    def moveToPosition(self, x=float, y=float, z=float, rz=float):
        try:
            HOST = self.host
            PORT = 30002
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            # move to position x,y,z
            a = "movel(p[" + str(x) + ", " + str(y) + ", " + str(z) + ", " + \
            str(0) + ", " + str(0) + ", " + str(rz) + "]," + " a=" + \
            str(self.linearacceleration) + ", v=" + str(self.linearvelocity) + ")" + "\n"
            print(a)
            s.send(a.encode())
            s.close()
        except Exception:
            print("Error move to setted position")

#-----------------------------------------------------------------------------------------------------------------------
    # define position of  object
    def setObjectPosition(self, dx = float, dy = float, rz = float):
        global pinceHeight,xMax,yMax,zMax,xMin,yMin,zMin
        self.object_posX = self.posx - dx
        self.object_posY = self.posy - CAMERA_DISTANCE - dy
        self.object_Rz = self.rz + rz
        print("angle is : " + str(rz) + " " + str(self.object_Rz))
        # should control what is the smallest and biggest reachable coordinates (for an object allowable position)
        if self.object_posX > xMax or self.object_posX < xMin or self.object_posY > yMax or self.object_posY < yMin:
            print("position is out of range")
#-----------------------------------------------------------------------------------------------------------------------
    def setObjectSize(self, x=float, y=float, z=float):
        global object_width_Max,object_height_Max,object_depth_Max
        self.object_width = x
        self.object_height = y
        self.object_depth = z

        if self.object_width > object_width_Max and self.object_height > object_height_Max and self.object_depth > object_depth_Max:
            print("Object is too big to hold")
#-----------------------------------------------------------------------------------------------------------------------
    def statePliers(self):
        if GPIO.input(pinceOut1) == 1 and GPIO.input(pinceOut2) == 0:
            self.master(EV_GRAB)
        if GPIO.input(pinceOut2) == 1 and GPIO.input(pinceOut1) == 0:
            self.master(EV_RELEASE)
#-----------------------------------------------------------------------------------------------------------------------
    # adjust openning of the pince,
    def adjustPince(self, choice):
        # if to close the pince
        if (choice == False):
            GPIO.output(pinceIn1, GPIO.LOW)  # tighten

        # if to open the pince
        else:
            GPIO.output(pinceIn1, GPIO.HIGH)  # loosen
#-----------------------------------------------------------------------------------------------------------------------
    # Take object for moving
    def catchObject(self):
        global  object_width_Max,object_height_Max
        if self.object_width < object_width_Max:
            # openning of pince in x-direction, adjust the openning
            print("go to position" + str(self.object_Rz))
            self.moveToPosition(self.object_posX, self.object_posY, self.posz,  self.object_Rz)
            # wait until arriving at position then do
            self.adjustPince(True)

        elif self.object_width > object_width_Max and self.object_height < object_height_Max:
            # openning of pince in y-direction, adjust the openning
            self.object_Rz = self.object_Rz + math.pi / 2
            print("go to position rot 90° " + str(self.object_Rz))
            self.moveToPosition(self.object_posX, self.object_posY, self.posz,  self.object_Rz)
            # wait until arriving at position then do
            self.adjustPince(True)
        else:
            print("Object is too big")

#-----------------------------------------------------------------------------------------------------------------------
    def master(self,event):
        global xSearch,ySearch,zSearch, rzSearch,xMin,yMin,zMin,xMax,yMax,zMax,MaxReached,ZeroReached, dX,dY ,evZone, lastZone ,BorderReached
        yMinSearch = -0.399
        yMaxSearch = -0.100
        dX = 0.05
        dY = 0.05
        #LED shows this part of the code is executed
        #GPIO.output(master, GPIO.HIGH)

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
                BorderReached = self.xSearch
                # go to zone 1 , zone one is the centeral part of the table
                if (BorderReached == 0 and self.ySearch == -0.300):
                    evZone = 1

                # go to zone 2, zone two is the right part of the table
                if evZone == 1 and self.ySearch == yMinSearch:
                    evZone = 2
                # go to zone 3, zone three is the left part of the table
                if ZeroReached <= (yMinSearch) and BorderReached == 0.200:
                    evZone = 3

                if (BorderReached == -0.200 and ZeroReached <= (yMinSearch - dY)):
                    print("search is complete")

                # Zone 1
                if evZone == 1:
                    if self.xSearch == 0 and self.ySearch == -0.200:
                        self.ySearch = yMinSearch
                    else:
                        self.ySearch = -0.200  # attention  not more than this (not less than |-200|)

                # Zone 2
                if evZone == 2:
                    # initialize the search in this zone
                    if lastZone == 1:
                        self.xSearch = dX
                        self.ySearch = yMinSearch
                        MaxReached = yMinSearch
                    # search in positive direction of y
                    if self.ySearch <= yMaxSearch and lastZone == evZone:
                        self.ySearch = self.ySearch + dY
                        if self.ySearch > yMaxSearch:  # set new value for x
                            self.xSearch = self.xSearch + dX
                            self.ySearch = yMaxSearch

                    # define new value for y in negative direction
                    if self.ySearch >= yMinSearch and lastZone == evZone:
                        self.ySearch = self.ySearch - dY
                        if self.ySearch < (yMinSearch - dY):  # set new value for x
                            self.xSearch = self.xSearch + dX
                            self.ySearch = yMinSearch

                # Zone 3
                if evZone == 3:
                    # initialize the search in this zone
                    if lastZone == 2:
                        self.xSearch = -dX
                        self.ySearch = yMinSearch
                    # search in positive direction of y
                    if self.ySearch <= yMaxSearch and lastZone == evZone:
                        self.ySearch = self.ySearch + dY
                        if self.ySearch > yMaxSearch:  # set new value for x
                            self.xSearch = self.xSearch - dX
                    # define new value for y in negative direction
                    if self.ySearch >= yMinSearch and lastZone == evZone:
                        self.ySearch = self.ySearch - dY
                        if self.ySearch < (yMinSearch - dY):  # set new value for x
                            self.xSearch = self.xSearch - dX
                            self.ySearch = yMinSearch

                lastZone = evZone

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
#-----------------------------------------------------------------------------------------------------------------------
    def reStart(self):
        #in event of repressing start-button, initialize the system then begin searching
        self.state = ST_INIT
        self.__init__()

#-----------------------------------------------------------------------------------------------------------------------
    def stop(self):
    #in event of pressing  stop-button, go to initial position and stop searching until new request
        self.theCamera.camera.stop_preview()
        self.__init__()
        self.calibrate()
        #LED turns off
        GPIO.output(led_In_Master, GPIO.LOW)


#-----------------------------------------------------------------------------------------------------------------------
    def getPins(self, pin =float):
        state = GPIO.gpio_function(pin)
        print(state)

#-----------------------------------------------------------------------------------------------------------------------
    def getPosition(self):
        x= self.posx
        y = self.posy
        z= self.posz
        rx = self.rx
        ry = self.ry
        rz = self.rz
        print(x)
        print(y)
        print(z)
        print(rx)
        print(ry)
        print(rz)

#-----------------------------------------------------------------------------------------------------------------------
    def getLinVelocity(self):
        linVelocity = self.linearvelocity
        print(linVelocity)
#-----------------------------------------------------------------------------------------------------------------------
    def getAngVelocity(self):
        angVelocity = self.angularvelocity
        print(angVelocity)

    def getAcceleration(self):
        linAcceleration = self.linearacceleration
        print(linAcceleration)
        angAcceleration = self.angularacceleration
#-----------------------------------------------------------------------------------------------------------------------
# Raspberry pin numbering method
#        GPIO.setmode(GPIO.BOARD)
#        GPIO.setwarnings(False)    #in case wanting to off the warning regarding pins
#        GPIO.setup(channel, GPIO.IN)
#        GPIO.setup(channel, GPIO.OUT)
#        GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)
#        GPIO.input(channel)        # read input value
#        GPIO.output(channel, state)# set output value   State can be 0 / GPIO.LOW / False or 1 / GPIO.HIGH / True.
#        GPIO.cleanup()
#        GPIO.cleanup(channel)
#        GPIO.cleanup( (channel1, channel2) )
#        GPIO.cleanup( [channel1, channel2] )