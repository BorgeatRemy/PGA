from scipy.spatial import distance as dist
from Factory import RobotControl
import Factory
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import math
from time import sleep
from picamera import PiCamera

class Camera():
    def __init__(self):
        self.deltaX_m = 0
        self.deltaY_m = 0
        self.angleRot_deg = 0
        self.pixelsPerMeter = None
        self.imgCrop = None
        self.robotController = None
        self.camera = None
    def initRelation(self,robotController):
        self.robotController = robotController
        self.camera = PiCamera()
    def capture(self):
        self.camera.resolution = (1024, 768)
        self.camera.start_preview()
        sleep(2)
        self.camera.capture("/home/pi/Documents/imageToAnalyse.jpg")
        self.camera.stop_preview()

    def cameraDetectionDice(self):
        numberDice = 0
        print("take picture")
        self.capture()
        print("picture taken")
        self.imgCrop = self.foundDice("/home/pi/Documents/imageToAnalyse.jpg",16)

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
                self.robotController.setObjectPosition(self.deltaX_m,self.deltaY_m,self.angleRot_deg)
                self.robotController.master(1)
        else:
            #generate event evNotFound
            print("dice dice not found")
            self.robotController.master(9)

    def detectNumberOnDice(self,image):
        nCircles = 0
        height, width, channel = image.shape

        # put the image in grayScale and blur it
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grayFilter = cv2.medianBlur(gray, 5)

        # search the circle in the image, search circle with radius between 1 and 2mm
        circles = cv2.HoughCircles(grayFilter, cv2.HOUGH_GRADIENT, 1, 50, param1=50, param2=30,
                                   minRadius=int(self.pixelsPerMeter), maxRadius=int(2 * self.pixelsPerMeter))
        if(circles is not None) :
            circles = np.uint16(np.around(circles))
        else :
            print("circles null")
        # count the circles
        for i in circles[0, :]:
            nCircles += 1

        return nCircles

    def midpoint(self,ptA, ptB):
        return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

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

        cv2.imwrite("/home/pi/PGA/Code/Edged.jpg",edged)

        # find contours in the edge map
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # 'pixels per metric' calibration variable
        pixelsPerMetric = None
        i = 0

        orig = image.copy()
        for c in cnts:

            # calculate the permiter and a approximation of the shape
            perimetre = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * perimetre, True)

            # if the area of the shape is too small or it's not a square/rectangle, just take the next shape
            if cv2.contourArea(c) < 100 or len(approx) != 4:
                continue

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

            if dA < dB + 6 and dA > dB - 6:  # dice seen right above it

                # if the pixels per metric has not been initialized, then
                # compute it as the ratio of pixels to supplied metric
                # (in this case, inches)
                if self.pixelsPerMeter is None:
                    self.pixelsPerMeter = dB / width_object

                # middle of the dice
                midX = tltrX + (blbrX - tltrX) / 2
                midY = tltrY + (blbrY - tltrY) / 2

                # rotation of the dice
                alpha = math.asin((blbrX - tltrX) / dA);
                self.angleRot_deg = round(math.degrees(alpha), 2)

                # calculate the vector to the center of the dice
                vectorAngle = -math.atan(midY / midX)
                vectorDistance = dist.euclidean((0, 0), (midX, midY))

                # rotate the entire image and keep the whole picture
                rotated = imutils.rotate_bound(image, self.angleRot_deg)
                width_rotated, height_rotated, channel_rotated = rotated.shape

                imageOrig_TopLeft_cornerX= 0
                imageOrig_TopLeft_cornerY= 0

                # calculcate the postion of the top left corner of the image after rotation
                if self.angleRot_deg > 0 and self.angleRot_deg < 180:
                    imageOrig_TopLeft_cornerX = math.sin(alpha) * height
                elif self.angleRot_deg < 0 and self.angleRot_deg > -180:
                    imageOrig_TopLeft_cornerY = -math.sin(alpha) * width

                # calulate the position of the dice center after rotation
                midX_rot = imageOrig_TopLeft_cornerX + vectorDistance * math.cos(vectorAngle - alpha)
                midY_rot = height_rotated - (imageOrig_TopLeft_cornerY - vectorDistance * math.sin(vectorAngle - alpha))

                # distance to the center of the dice from the middle of the image
                deltaX = midX_rot - width_rotated / 2
                deltaY = midY_rot - height_rotated / 2

                # distance to the center of the dice from the middle of the image in meter
                self.deltaX_m = round(deltaX / (1000 * self.pixelsPerMeter), 3)
                self.deltaY_m = round(deltaY / (1000 * self.pixelsPerMeter), 3)

                # crop the image to keep only the dice
                img_crop = rotated[int(midY_rot - dB / 2) + 15:int(midY_rot + dB / 2) - 15,
                           int(midX_rot - dA / 2) + 15:int(midX_rot + dA / 2) - 15]

                # return the dice
                return img_crop

        # dont find dice
        cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/orig.jpg", orig)
        return None

