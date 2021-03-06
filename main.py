# imports
import math
import cv2
import numpy as np
import threading
import time
from networktables import NetworkTables
import math
import json

# Robot networking code, makes program wait until network connection is confirmed to continue
cond = threading.Condition()
notified = [False]

# listen for a connection to the robot
def connectionListener(connected, info):
    print(info, '; Connected=%s' % connected)
    with cond:
        notified[0] = True
        cond.notify()

def setTableNumber(table,key,value):
    table.putNumber(key, value)  

# def compute_output_values(self, rvec, tvec):
#         '''Compute the necessary output distance and angles'''

#         x_r_w0 = np.matmul(RRTargetFinder2019.rot_robot, tvec) + RRTargetFinder2019.t_robot
#         x = x_r_w0[0][0]
#         z = x_r_w0[2][0]

#         # distance in the horizontal plane between robot center and target
#         distance = math.sqrt(x**2 + z**2)

#         # horizontal angle between robot center line and target
#         angle1 = math.atan2(x, z)

#         rot, _ = cv2.Rodrigues(rvec)
#         rot_inv = rot.transpose()

#         # location of Robot (0,0,0) in World coordinates
#         x_w_r0 = np.matmul(rot_inv, RRTargetFinder2019.camera_offset_rotated - tvec)

#         angle2 = math.atan2(x_w_r0[0][0], x_w_r0[2][0])

#         return distance, angle1, angle2


# Initialize NetworkTables and add a listener for until the connection has been established
NetworkTables.initialize(server='10.52.88.2')
NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)
visionTable = NetworkTables.getTable("SmartDashboard")

# as long as the Jetson has not connected, wait for a connection
'''with cond:
    print("Waiting")
    if not notified[0]:
        cond.wait()
'''
# At this point, the Jetson has connected.
print("Connected!")
visionTable.putNumber("YES!",-20)


# print out every item in an array, instead of using an ellipsis to shorten it.
np.set_printoptions(threshold=np.inf)

# define the HSV threshold ranges for the field retroreflective tape.
# vision tape green on table lighting values
#hue_range = [28, 85]
#saturation_range = [23, 255]
#value_range = [96, 255]
# keyon's room lighting values
#hue_range = [32,85]
#saturation_range = [0,40]
#value_range = [248,255]
# values used during calculation of focal length, for reference
hue_range = [66,76]
saturation_range = [202,255]
value_range = [213,255]
# 23.5 inches
# 24 inches = 60.96 cm
# chem class values
angleToTape = 0
#hue_range = [76,135]
#saturation_range = [5,77]
#value_range = [149,55]
# ics3u room 161 values, webcam
#hue_range = [100,120]
#saturation_range = [60,80]
#value_range = [120,180]
# test setup values, no green light
#hue_range = [39,99]
#saturation_range = [0,41]
#value_range = [233,255]
hue_range = [43,49]
saturation_range = [0,9]
value_range = [244,255]

hue_range = [0,125]
saturation_range = [0,10]
value_range = [227,255]
hue_range = [0,1]
saturation_range = [0,1]
value_range = [245,255]
hue_range = [80,120]
saturation_range = [20,115]
value_range = [192,255]

# distance between tapes constant
distanceBetweenTapes = 25.239
# Wait this long (in milliseconds) between iterations of the video stream.
wait_time = 2000

index = -1
thickness = 4
color = (255, 0, 255)

# angle per pixel
anglePerPixel = math.sqrt(1920**2 + 1080**2)

# ignore any detected object with a perimeter less than this.
perimeter_threshold = 35

# calculated with 30 cm data using F = (P x D) / H
# focal length of the Lifecam 3000
# F  = (75.9 x 60.96)/ 14.1
focal_length = 327.745

# height of the tape in centimetres
height_of_tape = 15
# The BGR (RGB but backwards because OpenCV handles it that way) colorspace is not good for isolating based on color.
# This is because the color is a combination of three different slots: blue, green, and red.
# The HSV colorspace refers to hue, saturation, and value. Hue describes the actual colour of the pixel.
# Since all the colour is in just one slot, it's a thousand times easier to isolate for colour using HSV.
def hsv_threshold(input, hue, saturation, value):
    """Segment an image based on hue, saturation, and value ranges.
    Args:
        input: A BGR numpy.ndarray.
        hue: A list of two numbers the are the min and max hue.
        saturation: A list of two numbers the are the min and max saturation.
        value: A list of two numbers the are the min and max value.
    Returns:
        A black and white numpy.ndarray.
    """
    # Convert the image to HSV
    out = cv2.cvtColor(input, cv2.COLOR_BGR2HSV)

    # this function goes through the input numpy.ndarray (the image)
    # and separates it based on its hsv values, according to my inputs.
    # it only returns HSV points that are within the range given in parameters. Returns them as a new image.
    return cv2.inRange(out, (hue[0], saturation[0], value[0]), (hue[1], saturation[1], value[1]))

# https://stackoverflow.com/questions/48109650/how-to-detect-two-different-colors-using-cv2-inrange-in-python-opencv
# draw the corners of the detected object. Takes in a cv2.boxPoints(rect) result
def drawCorners(points):
    # bottom right: points[0]
    cv2.circle(objects, (points[0][0], points[0][1]), 20, (255, 0, 0), thickness=1, lineType=8, shift=0)
    # bottom left: points[1]
    cv2.circle(objects, (points[1][0], points[1][1]), 20, (255, 0, 0), thickness=1, lineType=8, shift=0)
    # top left: points[2]
    cv2.circle(objects, (points[2][0], points[2][1]), 20, (255, 0, 0), thickness=1, lineType=8, shift=0)
    # top right: points[3]
    cv2.circle(objects, (points[3][0], points[3][1]), 20, (255, 0, 0), thickness=1, lineType=8, shift=0)

def getDistanceToCamera(minAreaRect,knownHeight, knownFocal, heightPixels):
    distance = -1
    if heightPixels > 0:
        distance = (knownHeight*knownFocal)/heightPixels
    return distance

def getAngleToTape(distances):
    for i in range(len(distances)):
        print("Distance",i,":",distances[i])
    angle = 0
    if 0 not in distances:
        try:
            angle = math.acos((-distances[0]**2 - distances[1]**2 + distanceBetweenTapes**2)/(-2*distances[0]*distances[1]))
        except ValueError:
            angle = -1
    if angle > 0:
        return angle
    return -1

# boolean logic to check if the detected object is the retroreflective tape.
def checkIfFound(check_perimeter, check_area, check_angle,check_height,check_width):
    #print("Perimeter:", check_perimeter,"\nArea:", check_area,"\nAngle:", check_angle)
    #print("Width:",check_width, "\nHeight:",check_height)
    # avoid division by zero
    if check_width > 0 and check_height > 0:
    #
        # find the ratio between height and width. As the rectangle is 5 by 2 inches, this should always be 2.5
        # But use this range to allow for inconsistency.
        # For the angles of the rect, it should be -78 and -12. This makes sense because OpenCV thinks of the box as on
        # a cartesian grid, turning counterclockwise. Why are both negative? Because the points OpenCV thinks is the
        # top left changes depending on the orientation (and therefore the angle!) of the rectangle.
        # For example, it might assign points[0] as the top left when really it should be points[2] how we see it.
        if 2 < check_height/check_width < 3 or 2 < check_width/check_height < 3 :
            # the angle for the vision tapes is 14.5 degrees
            if -20 < angle < -4 or 4 < angle < 20:
                print("FOUND, RIGHT!")
                return True
            elif -70 > angle > -90:
                print("FOUND, LEFT!")
                return True

        return False

# define the video camera (port 0)
cap = cv2.VideoCapture(0)

# "test" and other boolean logic is only here to quickly switch between taking in a single image vs.
# parsing an entire video feed.
test = True
with open('output.json') as json_file:
    data = json.load(json_file)
    # print(data)
    right_tape_world_coords = [[0,0,0],[5,1.1,0],[1.9,14.8,0],[-2.8,13.6,0],]

    right_tape_world_coords = [
    # Right target
    (3.938, 2.375, 0.0), # top left
    (5.875, 2.875, 0.0), # top right
    (7.313, -2.500, 0.0), # bottom left
    (5.375, -2.938, 0.0), # bottom right
    ]
    # right_tape_world_coordsUMat = cv2.UMat(np.array([[0,0,0],[5,1.1,0],[1.9,14.8,0],[-2.8,13.6,0]]))
    right_tape_world_coordsUMat = cv2.UMat(np.array(right_tape_world_coords))

    all_tape_world_coords = [
    # Left target
    (-5.938, 2.938, 0.0), # top left
    (-4.063, 2.375, 0.0), # top right
    (-5.438, -2.938, 0.0), # bottom left
    (-7.375, -2.500, 0.0), # bottom right

    # Right target
    (3.938, 2.375, 0.0), # top left
    (5.875, 2.875, 0.0), # top right
    (7.313, -2.500, 0.0), # bottom left
    (5.375, -2.938, 0.0), # bottom right
    ]
    all_tape_world_coordsUMat = cv2.UMat(np.array(all_tape_world_coords))    
    camera_matrix = data['camera_matrix']
    dist = data['distortion']
    while test:
        # test = False
        # take a frame from the video capture
        ret, bgr_img = cap.read()
        # read in the image
        # bgr_img = cv2.imread('testimages/retroreflectivetapegreen.jpg')
        if not ret:
            exit("Image retrieval failure")
        else:
            print(ret)
        # resize the image to half its original size
        imageResized = cv2.resize(bgr_img, (0, 0), fx=0.5, fy=0.5)
        # cv2.imshow("img",bgr_img)
        # cv2.imshow("resized",imageResized)
        # Gaussian blur the image, (191,191) refers to how much the image is being blurred on the X and Y axes.
        blurred_image = cv2.GaussianBlur(imageResized, (191, 191), 1)
        # cv2.imshow("BLURRED", blurred_image)

        # define the erosion kernel and erode the image
        # eroding eliminates inconsistencies between pixels, like small flares or bits
        # More iterations means a cleaner image, but takes a lot of processing power.
        kernel = np.ones((5, 5), 'uint8')
        erode = cv2.erode(blurred_image, kernel, iterations=3)

        # Run an HSV threshold on the image to isolate the retroreflective tape.
        thresholded_image = hsv_threshold(blurred_image, hue_range, saturation_range, value_range)
        # print(thresholded_image)

        # hierarchy refers to the tree of contours: whether a contour has contours inside it, etc.
        # contours is an array of the outsides of any detected object.
        # For example, contours[0] could be the outsides of a rectangle, while contours[1] could be a circle...
        # The x and y co-ordinates of every point on the contours is given as well.
        # by using cv2.RETR_EXTERNAL, we only take the top-level contours; no contours inside of contours, etc.
        contours, hierarchy = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # create an empty array (array of 0s) to draw the contours onto later.
        # An image in computer vision is just a 2D array with 3 channels: Think of a cartesian grid, but
        # with 3 values inside each point (for the pixel's colour)
        # Ex: [0][0] would mean the top-left corner of the image, and when you reference image[0][0]:
        # You get [blue,green,red], because image[0][0] is a pixel and [blue,green,red] are its values.
        # image.shape[0] is the height of the image (how many pixels)
        # image.shape[0] is the width of the image
        objects = np.zeros([thresholded_image.shape[0], thresholded_image.shape[1], 3], 'uint8')
        # loop through every object with contours
        fieldTapes = []
        lastFieldTapes = 0
        # save the distances across each iteration, 0 and 1
        distancesToTape = []
        # save the angle to the tape, calculated via cosine law
        for c in contours:
            # calculate the area of the object
            area = cv2.contourArea(c)
            # calculate the perimeter of the object
            perimeter = cv2.arcLength(c, True)

            if perimeter > perimeter_threshold:
                cv2.drawContours(objects, [c], -1, color, 1)
                # draw contours of the thresholded image one by one, do not do the inner fill of the image
                M = cv2.moments(c)

                # centroid: exact middle points
                # cx = int(M['m10']/M['m00'])
                # cy = int(M['m01']/M['m00'])
                # cv2.circle(objects, (cx,cy), 4, (0,0,255),-1)

                # print("Area: {}, perimeter: {}".format(area,perimeter))
                #print(contours)
                rect = cv2.minAreaRect(c)
                # get rectangle information
                # https://stackoverflow.com/questions/36293335/using-bounding-rectangle-to-get-rotation-angle-not-working-opencv-python
                center = rect[0]
                angle = rect[2]
                #rot = cv2.getRotationMatrix2D(center, angle - 90, 1)
                #print("Angle: ",angle)
                # img = cv2.warpAffine(img, rot, (rows, cols))

                # this converts the given rect to the main 4 corners of the rect
                box = cv2.boxPoints(rect)
                points = cv2.boxPoints(rect)
                # d = math.sqrt(tx*tx + ty*ty + tz*tz)

                #  modify the data type of the array, convert to integers
                box = np.int0(box)
                # draw the contours of the box
                cv2.drawContours(objects, [box], 0, (0, 0, 255), 2)

                # define the 4 corners of the rectangle
                bottom_left = points[1]
                bottom_right = points[0]
                top_left = points[2]
                top_right = points[3]
                # use cartesian grid math to figure out the width and height of the rectangles:
                # distance = sqrt((x1-x2)^2 + (y1-y2)^2)
                width_in_pixels = math.sqrt((bottom_left[0] - bottom_right[0]) ** 2 + (bottom_left[1] - bottom_right[1]) ** 2)
                height_in_pixels = math.sqrt((bottom_left[0]-top_left[0])**2 + (bottom_left[1]-top_left[1])**2)
                largest_y = 0
                smallest_y = 100000
                for i in points:
                    if i[1] > largest_y:
                        largest_y = i[1]
                    if i[1] < smallest_y:
                        smallest_y = i[1]
                total_vertical_height = largest_y - smallest_y

                # Depending on whether the rectangle is being laid flat (imagine the x-axis) vs. being laid out upwards (y-axis),
                # OpenCV will switch between width and height as it'll start counting from a different corner.
                # If the angle given by OpenCV is negative, then the rectangle is laid out flat, and width will be calculated as if it's height.
                # Switch the two if this happens!

                # print out data
                # print("Bottom left and bottom right (used to calc width): ", bottom_left, bottom_right)
                # print("Bottom left and top left (used to calc height): ", bottom_left, top_left)
                # print("Width: ", width_in_pixels)
                # print("Height: ", height_in_pixels)
                # print("Area:", area)
                # print("Angle:", angle)
                # print("Perimeter:",perimeter)
                # print("All four corners: ")
                # print("Bottom left:",bottom_left)
                # print("Bottom right:",bottom_right)
                # print("Top left:",top_left)
                # print("Top right:",top_right)
                # print("Total vertical height: ", total_vertical_height)

                # (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), rvec, tvec, camera_matrix, dist)
                
                # # for p in image_points:
                # #     cv2.circle(im, (int(p[0]), int(p[1])), 3, (0,0,255), -1)
                
                
                # p1 = ( int(points[0][0]), int(points[0][1]))
                # p2 = ( int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
                
                # cv2.line(objects, p1, p2, (255,0,0), 2)
                # if the rectangle is found, then add it to a list of the field tapes so we can compare the two field tapes later
                if checkIfFound(perimeter,area,angle,height_in_pixels,width_in_pixels):
                    fieldTapes.append(rect)

                    distancesToTape.append(getDistanceToCamera(rect,height_of_tape,focal_length,total_vertical_height))

                    print("Distance:",getDistanceToCamera(rect,height_of_tape,focal_length,total_vertical_height))
                    if len(distancesToTape) > 1:
                        print(distancesToTape[0])
                        print(distancesToTape[1])
                    if len(distancesToTape) >= 2:
                        angleToTape = getAngleToTape(distancesToTape)
                    print("Angle to tape:", angleToTape)
                    print("Image center:", thresholded_image.shape[1]/2, thresholded_image.shape[0]/2)

                    # draw the corners of the rectangle and check if it's the field's vision target
                    drawCorners(points)

                # print("\n")
                #cv2.putText(objects, ("Distance:" + getDistanceToCamera(rect,height_of_tape,focal_length,total_vertical_height)) ), (top_left[0],top_left[1]), cv2.FONT_HERSHEY_COMPLEX, 2, 255)

            if(len(fieldTapes) == 2):
                print("--SOLVEPNP  START--")
                print('Camera matrix: ',camera_matrix)
                print('Distortion matrix:',dist)
                all_image_points = []
                for x in fieldTapes:
                    all_image_points.extend(cv2.boxPoints(rect))
                print("Recorded image points:",all_image_points)
                all_image_points = cv2.UMat(np.array(all_image_points))
                retval, rvec, tvec = cv2.solvePnP(all_tape_world_coordsUMat,all_image_points,cv2.UMat(np.array(camera_matrix)), cv2.UMat(np.array(dist)))

                print("RETVAL,RVEC,TVEC:")
                print(retval)
                print(rvec.get())
                print(tvec.get()) 
                print()

                
                # Compute the necessary output distance and angles
                x = tvec.get()[0][0]
                y = tvec.get()[1][0]
                z = tvec.get()[2][0]
                # distance in the horizontal plane between camera and target
                distance = math.sqrt(x**2 + z**2)
                # horizontal angle between camera center line and target
                angle1 = math.atan2(x, z)
                rot, _ = cv2.Rodrigues(rvec.get())
                rot_inv = rot.transpose()
                pzero_world = np.matmul(rot_inv, -tvec.get())
                angle2 = math.atan2(pzero_world[0][0], pzero_world[2][0])
                print ("Distance: %f, Angle1: %f, Angle2: %f, X: %f, Y: %f, Z: %f" % (distance, angle1, angle2, x, y, z))
            else:
                print("Two field tapes NOT found.")
                print()

            # # To save from hundreds of printouts, only print out number of field tapes detected if it has changed.
            # if(len(fieldTapes) != lastFieldTapes):
            #     lastFieldTapes = len(fieldTapes)
            #     print('Number of tapes:',len(fieldTapes))

        # Wait 50 milliseconds between iterations.
        given_key = cv2.waitKey(wait_time)
        # Break ifg
        if given_key == ord('x'):
            break

        # time.sleep(200)
        # show images
        cv2.imshow("Thresholded", thresholded_image)
        cv2.imshow("Objects", objects)
        #cv2.imshow("Original", imageResized)

    # release the camera input and end the program, destroying all windows
    cap.release()
    cv2.destroyAllWindows()
