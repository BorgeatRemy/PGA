from scipy.spatial import distance as dist
from RobotControl import RobotControl
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import math
from time import sleep
from picamera import PiCamera
## @package camera
# perform image analysis

##take a picture and anlyse it to detect a dice
class Camera():
    ##the constructor
    def __init__(self):
        ##delta x of the object in meter from the center of the camera
        self.deltaX_m = 0
        ##delta y of the object in meter from the center of the camera
        self.deltaY_m = 0
        ##orientation the object in radian
        self.angleRot = 0
        ##pixels per meter ration
        self.pixelsPerMeter = None
        ##image of the dice
        self.imgCrop = None
        ##robotController object
        self.robotController = None
        ##camera object
        self.camera = None

        #init the camera
        self.camera = PiCamera()
        self.camera.resolution = (3280, 2464)
        self.camera.start_preview()
        sleep(2)

    ## intialise relation
    #  @param self The object pointer.
    #  @param self The robot controller object
    def initRelation(self,robotController):
        self.robotController = robotController

    ## capture an image
    #  @param self The object pointer.
    def capture(self):
        self.camera.capture("/home/pi/PGA/imageToAnalyse2.jpg")

    ## manage the dice detection
    #  then trigger the state machine of class RobotControl depending
    #  on the dice number
    #  @param self The object pointer.
    def cameraDetectionDice(self):
        numberDice = 0
        print("take picture")
        self.capture()
        print("picture taken")
        self.imgCrop = self.foundDice("/home/pi/PGA/imageToAnalyse2.jpg",16)

        if(self.imgCrop is not None) :
            print("dice found")
            numberDice = self.detectNumberOnDice(self.imgCrop)
            if(numberDice == 6):
                #generate ev6
                print("6 found")
                self.robotController.master(2)
            else:
                #generate evFound
                print("dice found, not 6")
                self.robotController.setObjectPosition(self.deltaX_m,self.deltaY_m,self.angleRot)
                print("(dx,dy): " + str(self.deltaX_m*1000) + ":" + str(self.deltaY_m*1000))
                self.robotController.master(1)
        else:
            #generate event evNotFound
            print("dice dice not found")
            self.robotController.master(9)

    ## detect the number on a dice
    #  @param self The object pointer.
    #  @param image image of the dice
    #  @return the dice number
    def detectNumberOnDice(self,image):
        nCircles = 0
        # put the image in grayScale and blur it
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grayFilter = cv2.medianBlur(gray, 5)

        # search the circle in the image, search circle with radius between 1 and 2mm
        circles = cv2.HoughCircles(grayFilter, cv2.HOUGH_GRADIENT, 1, 50, param1=50, param2=30,
                                   minRadius=int(self.pixelsPerMeter), maxRadius=int(2 * self.pixelsPerMeter))
        if(circles is not None) :
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                nCircles += 1
            print("Dice number : " + str(nCircles))
        else :
            print("circles null")
        # count the circles

        return nCircles

    ## calculate the mid point between 2 points
    #  @param self The object pointer.
    #  @param ptA point 1
    #  @param ptB point 2
    #  @return the middle point
    def midpoint(self,ptA, ptB):
        return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

    ## search a dice in an image
    #  @param self The object pointer.
    #  @param imagePath path to the image
    #  @param width_object width in mm of the object
    #  @return an image of the dice
    def foundDice(self,imagePath, width_object):
        image = cv2.imread(imagePath)

        background = 0

        # Converting the color space from BGR to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Generating mask to detect color only
        lower_white = np.array([0, 0, 0])
        upper_white = np.array([255, 150, 255])
        mask1 = cv2.inRange(hsv, lower_white, upper_white)

        # Refining the mask corresponding to the detected red color
        mask1 = cv2.morphologyEx(mask1, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=2)
        mask1 = cv2.dilate(mask1, np.ones((3, 3), np.uint8), iterations=1)

        height, width = mask1.shape

        # perform canny edge detection
        edged = cv2.Canny(mask1, 40, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        # find contours in the edge map
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        for c in cnts:

            # if the area of the shape is too small or it's not a square/rectangle, just take the next shape
            if cv2.contourArea(c) < 25000:
                continue

            orig = image.copy()

            # compute the rotated bounding box of the contour
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")

            # order the points in the contour such that they appear
            # in top-left, top-right, bottom-right, and bottom-left
            # order, then draw the outline of the rotated bounding
            # box
            box = perspective.order_points(box)
            cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

            # loop over the original points and draw them
            for (x, y) in box:
                cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)

            # unpack the ordered bounding box, then compute the midpoint
            # between the top-left and top-right coordinates, followed by
            # the midpoint between bottom-left and bottom-right coordinates
            (tl, tr, br, bl) = box
            (tltrX, tltrY) = self.midpoint(tl, tr)
            (blbrX, blbrY) = self.midpoint(bl, br)

            # compute the midpoint between the top-left and top-right points,
            # followed by the midpoint between the top-righ and bottom-right
            (tlblX, tlblY) = self.midpoint(tl, bl)
            (trbrX, trbrY) = self.midpoint(tr, br)

            # compute the Euclidean distance between the midpoints
            dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
            dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

            if dA < dB + 5 and dA > dB - 5 :  # dice seen right above it

                # if the pixels per metric has not been initialized, then
                # compute it as the ratio of pixels to supplied metric
                # (in this case, inches)
                if self.pixelsPerMeter is None:
                    self.pixelsPerMeter = dB / width_object

                # middle of the dice
                midX = tltrX + (blbrX - tltrX) / 2
                midY = tltrY + (blbrY - tltrY) / 2

                # rotation of the dice
                self.angleRot = math.asin((blbrX - tltrX) / dA);
                angleRot_deg = round(math.degrees(self.angleRot), 2)

                # calculate the vector to the center of the dice
                vectorAngle = -math.atan(midY / midX)
                vectorDistance = dist.euclidean((0, 0), (midX, midY))

                # rotate the entire image and keep the whole picture
                rotated = imutils.rotate_bound(image, angleRot_deg)

                imageOrig_TopLeft_cornerX= 0
                imageOrig_TopLeft_cornerY= 0

                # calculcate the postion of the top left corner of the image after rotation
                if angleRot_deg > 0 and angleRot_deg < 180:
                    imageOrig_TopLeft_cornerX = math.sin(self.angleRot) * height
                elif angleRot_deg < 0 and angleRot_deg > -180:
                    imageOrig_TopLeft_cornerY = -math.sin(self.angleRot) * width

                # calulate the position of the dice center after rotation
                midX_rot = imageOrig_TopLeft_cornerX + vectorDistance * math.cos(vectorAngle - self.angleRot)
                midY_rot = imageOrig_TopLeft_cornerY - vectorDistance * math.sin(vectorAngle - self.angleRot)

                # distance to the center of the dice from the middle of the image
                deltaX = midX - width / 2
                deltaY = height / 2 - midY

                # distance to the center of the dice from the middle of the image in meter
                self.deltaX_m = round(deltaX / (1000 * self.pixelsPerMeter), 6)
                self.deltaY_m = round(deltaY / (1000 * self.pixelsPerMeter), 6)

                # crop the image to keep only the dice
                img_crop = rotated[int(midY_rot - dB / 2) + 15:int(midY_rot + dB / 2) - 15,
                           int(midX_rot - dA / 2) + 15:int(midX_rot + dA / 2) - 15]

                # return the dice
                return img_crop

        # dont find dice
        return None

