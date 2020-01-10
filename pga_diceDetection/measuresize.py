# import the necessary packages
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import math


def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


def detectNumberOnDice(image,pixelsperMetrics):
    nCircles = 0
    height, width,channel = image.shape
    #put the image in grayScale and blur it
    cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/imagecrop.jpg", image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    grayFilter = cv2.medianBlur(gray,5)

    # search the circle in the image, search circle with radius between 1 and 2mm
    circles = cv2.HoughCircles(grayFilter, cv2.HOUGH_GRADIENT, 1, 50,param1=50, param2=30, minRadius=int(pixelsperMetrics), maxRadius=int(2*pixelsperMetrics))
    circles = np.uint16(np.around(circles))

    #count the circles
    for i in circles[0, :]:
        nCircles +=1

    return nCircles

def foundDice(imagePath, width_object):
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

    cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/mask1.jpg", mask1)

    height, width = mask1.shape

    #perform canny edge detection
    edged = cv2.Canny(mask1, 40, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/edged.jpg", edged)

    # find contours in the edge map
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    # sort the contours from left-to-right and initialize the
    (cnts, _) = contours.sort_contours(cnts)


    # 'pixels per metric' calibration variable
    pixelsPerMetric = None
    i = 0

    orig = image.copy()
    for c in cnts:

        #calculate the permiter and a approximation of the shape
        perimetre = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * perimetre, True)

        #if the area of the shape is too small or it's not a square/rectangle, just take the next shape
        if cv2.contourArea(c) < 100 or len(approx) !=4:
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
        (tltrX, tltrY) = midpoint(tl, tr)
        (blbrX, blbrY) = midpoint(bl, br)

        # compute the midpoint between the top-left and top-right points,
        # followed by the midpoint between the top-righ and bottom-right
        (tlblX, tlblY) = midpoint(tl, bl)
        (trbrX, trbrY) = midpoint(tr, br)

        # compute the Euclidean distance between the midpoints
        dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
        dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))


        if dA < dB + 6 and dA > dB - 6  : #dice seen right above it

            # if the pixels per metric has not been initialized, then
            # compute it as the ratio of pixels to supplied metric
            # (in this case, inches)
            if pixelsPerMetric is None:
                pixelsPerMetric = dB / width_object
                height_m = height / (1000*pixelsPerMetric)
                width_m = width / (1000*pixelsPerMetric)
                print(str(height_m) + " " + str(width_m))

            #dimension of the object in meter with a 1 mm precision
            dimA_m = round(dA/(1000*pixelsPerMetric), 3)
            dimB_m = round(dB/(1000*pixelsPerMetric), 3)

            #middle of the dice
            midX = tltrX + (blbrX - tltrX) / 2
            midY = tltrY + (blbrY - tltrY) / 2

            #middle of the dice in meter
            midX_m = round(midX/(1000 * pixelsPerMetric), 3)
            midY_m = height_m - round(midY/(1000*pixelsPerMetric), 3)

            #distance to the center of the dice from the middle of the image
            deltaX_m = midX_m - width_m / 2
            deltaY_m = midY_m - height_m / 2

            #rotation of the dice
            alpha = math.asin((blbrX - tltrX) / dA);
            alpha_deg = round(math.degrees(alpha), 2)

            # calculate the vector to the center of the dice
            vectorAngle = -math.atan(midY / midX)
            vectorDistance = dist.euclidean((0, 0), (midX, midY))

            print("object number " + str(i) + " pos(x,y) : " + str(midX) + "," + str(midY) + " (w,h) : " + str(
                dA) + "," + str(dB) + " angle : " + str(alpha_deg) + "delta(x,y)" + str(deltaX_m) + "," + str(deltaY_m))
            print(str(width) + " : " + str(height))

            #rotate the entire image and keep the whole picture
            rotated = imutils.rotate_bound(image, alpha_deg)
            cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/img_rot.jpg", rotated)

            posX = 0
            posY = 0

            #calculcate the postion of the top left corner of the image after rotation
            if alpha_deg > 0 and alpha_deg < 180:
                posY = 0
                posX = math.sin(alpha) * height
            elif alpha_deg < 0 and alpha_deg > -180:
                posY = -math.sin(alpha) * width
                posX = 0

            #calulate the position of the dice center after rotation
            midX_rot = posX + vectorDistance * math.cos(vectorAngle - alpha)
            midY_rot = posY - vectorDistance * math.sin(vectorAngle - alpha)

            print(str(vectorDistance) + " : " + str(vectorAngle))
            print("new x,y " + str(midX_rot) + ":" + str(midY_rot) + "pos(X,Y) : " + str(posX) + " : " + str(posY))

            #crop the image to keep only the dice
            img_crop = rotated[int(midY_rot - dB / 2)+15:int(midY_rot + dB / 2)-15,
                       int(midX_rot - dA / 2)+15:int(midX_rot + dA / 2)-15]

            cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/img_crop.jpg", img_crop)
            cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/orig.jpg", orig)

            #return the dice
            return img_crop,pixelsPerMetric

    #dont find dice
    cv2.imwrite("C:/Users/rebor/PycharmProjects/PGA/orig.jpg", orig)
    return None, None