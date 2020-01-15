from Factory import RobotControl
from Camera import Camera
from threading import Thread
from threading import Timer
import math
import RPi.GPIO as GPIO

#setup pins for buttons, define states and events
button_Start = 29
button_Stop = 22
led_Start = 36
GPIO.setmode(GPIO.BOARD)
GPIO.setup(button_Start, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(button_Stop, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led_Start, GPIO.OUT)
GPIO.output(led_Start, GPIO.LOW)

# assigne states and events
STATE_INIT = 0
STATE_START = 1
STATE_STOP = 2
EV_INIT = 0
EV_START = 1
EV_STOP = 2

state = STATE_INIT
oldState = 0
def getData():
    obj2 = RobotControl_Thread()
    obj2.daemon = True
    obj2.start()
    obj2.join()
if __name__ == "__main__":
    theRobotController = RobotControl()

    theCamera = Camera()
    theCamera.initRelation(theRobotController)

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
            state = STATE_INIT

    #States operations
    if oldState != state:
        if state == STATE_INIT:
            if oldState == STATE_STOP:
                theRobotController.reStart()
        if state == STATE_START:
            theRobotController.initRelations(theCamera)
            theRobotController.adjustPince(False)
            theRobotController.master(EV_INIT)
        # GPIO.output(led_Start, GPIO.HIGH)

        if state == STATE_STOP:
            theRobotController.stop()
#-----------------------------------------------------------------------------------------------------------------------
def callbackStart(channel):
    stateMachine(EV_START)
    print("start")
def callbackStop(channel):
    stateMachine(EV_STOP)
    print("stop")

GPIO.add_event_detect(button_Start, GPIO.RISING, callback=callbackStart, bouncetime=300)
GPIO.add_event_detect(button_Stop, GPIO.RISING, callback=callbackStop, bouncetime=300)

class RobotControl_Thread(Thread):
    def __init__(self):
        Thread.__init__(self)
        theRobotController.updateCurrentPosition()

    def run(self):
        global i
        i+=1
        theRobotController.updateCurrentPosition()
        if(theRobotController.takeOrRelease==True):
            theRobotController.statePliers()
while (True):
    t = Timer(0.1,getData)
    t.start()
    t.join()




