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

def imageNumberOnDice(image,width):
    height,width,channel = image.shape

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    edged = cv2.Canny(gray, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)
    cv2.imshow("rdged",edged) 
    # find contours in the edge map
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
     
    # sort the contours from left-to-right and initialize the
    # 'pixels per metric' calibration variable
    (cnts, _) = contours.sort_contours(cnts)
    pixelsPerMetric = None
    i = 0
    # loop over the contours individually
    for c in cnts:
        # if the contour is not sufficiently large, ignore it
        if cv2.contourArea(c) < 50:
            continue
        i = i + 1
    return i

def imageFoundDice(imagePath,width_object): 
    image = cv2.imread(imagePath)
    height,width,channel = image.shape

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    edged = cv2.Canny(gray, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)
    cv2.imshow("rdged",edged) 
    # find contours in the edge map
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
     
    # sort the contours from left-to-right and initialize the
    # 'pixels per metric' calibration variable
    (cnts, _) = contours.sort_contours(cnts)
    pixelsPerMetric = None
    i = 0
    for c in cnts:
        # if the contour is not sufficiently large, ignore it
        if cv2.contourArea(c) < 100:
            continue
        # compute the rotated bounding box of the contour
        orig = image.copy()
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
     
        midX = tltrX + (blbrX - tltrX) / 2
        midY = tltrY + (blbrY - tltrY) / 2

        # compute the Euclidean distance between the midpoints
        dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
        dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
         
        # if the pixels per metric has not been initialized, then
        # compute it as the ratio of pixels to supplied metric
        # (in this case, inches)
        if pixelsPerMetric is None:
            pixelsPerMetric = dB / width_object
            height_m = height / pixelsPerMetric
            width_m = width / pixelsPerMetric
            print(str(height_m) + " " + str(width_m))
       
       # compute the size of the object
        dimA = dA / pixelsPerMetric
        dimB = dB / pixelsPerMetric
     
        # show the output image
        i = i+1
        dimA_m = round(dimA,3)
        dimB_m = round(dimB ,3)
        midX_m = round(midX / pixelsPerMetric,3)
        midY_m = height_m - round(midY / pixelsPerMetric,3)
       
        deltaX = midX_m - width_m/2
        deltaY = midY_m - height_m/2
        alpha = math.asin((blbrX - tltrX) / dA);
        alpha_deg = round(math.degrees(alpha),2)
        
        #calculate the vector to the center of the dice
        vectorAngle = -math.atan(midY/midX)
        vectorDistance = dist.euclidean((0,0),(midX,midY))
        
        cv2.imshow("Image", orig)
        
        print("object number " + str(i) + " pos(x,y) : " + str(midX)+ "," + str(midY) + " (w,h) : " + str(dimA_m) +  "," + str(dimB_m) + " angle : " + str(alpha_deg) + "delta(x,y)" + str(deltaX) + "," + str(deltaY))
        print(str(width) + " : " + str(height))

        rotated = imutils.rotate_bound(orig,alpha_deg)
        
        cv2.imshow("img-rotated",rotated)
        posX = 0
        posY = 0
        
        if alpha_deg > 0 and alpha_deg < 180 :
            posY = 0
            posX = math.sin(alpha) * height
        elif alpha_deg < 0 and alpha_deg > -180:
            posY = -math.sin(alpha) * width
            posX = 0

        midX_rot = posX + vectorDistance * math.cos(vectorAngle-alpha)
        midY_rot = posY - vectorDistance * math.sin(vectorAngle-alpha)

        print(str(vectorDistance) + " : " + str(vectorAngle))
        print("new x,y " + str(midX_rot) + ":" + str(midY_rot) + "pos(X,Y) : " + str(posX) + " : " + str(posY))
        img_crop = rotated[int(midY_rot-dB/2)+10:int(midY_rot+dB/2)-10,int(midX_rot-dA/2)+10:int(midX_rot+dA/2)-10]
        
        cv2.imshow("img-crop",img_crop)
        
        cv2.waitKey(10000)
        return img_crop

