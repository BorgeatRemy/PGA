from RobotControl import RobotControl
from Camera import Camera
from threading import Thread
from threading import Timer
import math
import RPi.GPIO as GPIO
## @package main
# main of the program

#setup pins for buttons, define states and events
BUTTON_START = 29
BUTTON_STOP = 22
LED_START = 36
LED_STOP = 40       #Red led to show when the robot is stopped

# assigne states and events
STATE_INIT = 0
STATE_START = 1
STATE_STOP = 2
EV_INIT = 0
EV_START = 1
EV_STOP = 2

##actual state for the state machine
state = STATE_INIT

##old state for the state machine
oldState = STATE_INIT

##launch robotController Thread
def getData():
    obj2 = RobotControl_Thread()
    obj2.daemon = True
    obj2.start()
    obj2.join()


## stateMachine
#  manage the state of the soft : init, running, stop
#  @param ev event to trigger the state machine
def stateMachine(ev=int):
    global state
    global oldState
    oldState = state
    #State machine changes
    if state == STATE_INIT:
        if ev == EV_START:
            state = STATE_START
    elif state == STATE_START:
        print("State start")
        if ev == EV_STOP:
            state = STATE_STOP
    elif state == STATE_STOP:
        print("State stop")
        if ev == EV_START:
            state = STATE_INIT

    #States operations
    if oldState != state:
        if state == STATE_INIT:
            if oldState == STATE_STOP:
                GPIO.output(LED_START, GPIO.HIGH)
        if state == STATE_START:
            theRobotController.initRelations(theCamera)
            theRobotController.adjustPince(False)
            theRobotController.master(EV_INIT)
            GPIO.output(LED_START, GPIO.HIGH)
        if state == STATE_STOP:
            print("go in stop state")
            theRobotController.stop()
## function called when button start pressed
def callbackStart(channel):
    stateMachine(EV_START)
    print("start")

## function called when button stop pressed
def callbackStop(channel):
    stateMachine(EV_STOP)
    print("stop")

##Class RobotControl_Thread update postion of the robot
class RobotControl_Thread(Thread):
    ## the constructor
    def __init__(self):
        Thread.__init__(self)
    ## get position of the robot
    def run(self):
        theRobotController.updateCurrentPosition()
        if(theRobotController.takeOrRelease==True):
            theRobotController.statePliers()

##main of the soft
if __name__ == "__main__":
    #Gpio setup
    GPIO.setmode(GPIO.BOARD)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(BUTTON_START, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(BUTTON_STOP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(LED_START, GPIO.OUT)
    GPIO.setup(LED_STOP, GPIO.OUT)
    GPIO.output(LED_STOP, GPIO.LOW)

    #Gpio add event for button start and stop
    GPIO.add_event_detect(BUTTON_START, GPIO.RISING, callback=callbackStart, bouncetime=200)
    GPIO.add_event_detect(BUTTON_STOP, GPIO.RISING, callback=callbackStop, bouncetime=200)

    ##class RobotControl object
    theRobotController = RobotControl()

    ##class Camera object
    theCamera = Camera()

    #init relation bewteen camera and robot controller
    theCamera.initRelation(theRobotController)

while (True):
    ##timer to launch thread periodically
    t = Timer(0.1,getData)
    t.start()
    t.join()




