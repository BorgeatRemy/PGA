import measuresize
import cv2
import argparse
def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True,
                    help="path to the input image")
    ap.add_argument("-w", "--width", type=float, required=True,
                    help="width of the left-most object in the image (in inches)")
    args = vars(ap.parse_args())

    image_crop,pixelsPerMetric = measuresize.foundDice(args["image"], args["width"])
    if image_crop is not None :
        diceNumber = measuresize.detectNumberOnDice(image_crop, pixelsPerMetric)
        print(str(diceNumber))
    else:
        print("no dice found")



if __name__=="__main__":
    run()