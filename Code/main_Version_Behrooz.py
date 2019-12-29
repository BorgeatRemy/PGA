from Factory import RobotControl
from threading import Thread
from threading import Timer
import math
import RPi.GPIO as GPIO

#setup pins for buttons, define states and events
button_Start = 38
button_Stop =  40
GPIO.setmode(GPIO.BOARD)
GPIO.setup(button_Start, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button_Stop, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# assigne states and events
STATE_INIT = 0
STATE_START = 1
STATE_STOP = 2
EV_INIT = 0
EV_START = 1
EV_STOP = 2

state = 0
oldState = 0
def getData():
    obj2 = RobotControl_Thread()
    obj2.daemon = True
    obj2.start()
    obj2.join()
if __name__ == "__main__":
    theRobotController = RobotControl()
   # theRobotController.calibrate()
    i = 0
    theRobotController.nextX = 100

#-----------------------------------------------------------------------------------------------------------------------
def stateMachine(ev=int):
    global state
    global oldState
    oldState = state
    #State machine changes
    if state == STATE_INIT:
        if ev == EV_START:
            state = STATE_START

    elif state == STATE_START:
        if ev == EV_STOP:
            state = STATE_STOP

    elif state == STATE_STOP:
        if ev == EV_START:
            state == STATE_INIT
        if ev == EV_STOP:
            doNothing = 0

    #States operations
    if oldState != state:
        if state == STATE_INIT:
            if oldState == STATE_STOP:
                theRobotController.reStart()

        if state == STATE_START:
            theRobotController.master()

        if state == STATE_STOP:
            theRobotController.stop()
#-----------------------------------------------------------------------------------------------------------------------
class RobotControl_Thread(Thread):
    def __init__(self):
        Thread.__init__(self)
        #stateMachine(EV_INIT)
        theRobotController.updateCurrentPosition()
        theRobotController.master(EV_INIT)

    def run(self):
        global i
        i+=1
        theRobotController.updateCurrentPosition()
        if(theRobotController.takeOrRelease==True):
            theRobotController.statePliers()
        # buttons change state of operations
        if GPIO.output(button_Start, GPIO.HIGH):
            stateMachine(EV_START)
        if GPIO.output(button_Stop, GPIO.HIGH):
           stateMachine(EV_STOP)

while (True):
    t = Timer(0.5,getData)
    t.start()
    t.join()




