import measuresize
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
    help="path to the input image")
ap.add_argument("-w", "--width", type=float, required=True,
    help="width of the left-most object in the image (in inches)")
args = vars(ap.parse_args())

image_crop = measuresize.imageFoundDice(args["image"],args["width"])
diceNumber = measuresize.imageNumberOnDice(image_crop,args["width"])

print(str(diceNumber))
