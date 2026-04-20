# Generates an array of hexagonal objects following the game engine polygon definition from
# the object data in the format seen in "objects.txt" that is sent by the cybot when it scans or detects
# a hole, border, or short object.
# Will have to code into the game engine the relative camera position, edge cases, and overwriting objects
# Author: Noah Peterson
# Modified: 12/11/2025 - documentation
import os
import numpy as np


def generate_objects(camera, height):
    absolute_path = os.path.dirname(__file__) # Absolute path to this python script
    relative_path = "./" 
    full_path = os.path.join(absolute_path, relative_path) # Full path to sensor data file

    logfile_filename = "objects.txt"
    object_array_output_filename = "object-defs.txt"

    logfile = open(full_path + logfile_filename, 'r')
    file_header = logfile.readline() # Read and store the header into file_header
    nextline = logfile.readline().strip() # Reads first line. If objects were detected it will contain info about the first object, otherwise be empty. Strips newline character.
    file_data = []

    # no objects detected
    if (nextline == ""):
        out_file = open(object_array_output_filename, 'w')
        out_file.write("None")
        out_file.close()
        return


    # store initial object information filedata
    while ((nextline.split())[0].strip() != "Object"):  # stores lines until PING data begins
        file_data.append(nextline)
        nextline = logfile.readline()

    # store lines containing PING distance in other list
    distance_info = [nextline]              # first line was read at the end of the loop
    distance_info += logfile.readlines()     # read the rest of the lines


    # strip newline characters
    for index, i in enumerate(distance_info):
        distance_info[index] = i.strip()

    logfile.close()

    print(distance_info)

    if (len(file_data) == 0):
        exit


    # parse data into expected structure of polygon vertices: [x, z, facing, height]. 
    # for now, x and y will be only relative to 0, 0. facing will always be out.
    # creates a hexagon to represent cylindrical object. vertices connect in clockwise fashion

    # def of normalized hexagon in the order of drawn. game engine says clockwise but it comes out mirrored along the x axis, 
    # so its essentially ccw. im really not sure but it works.
    # 0, -1 is the closest point to the camera
    base_hexagon = np.array([
        [0, -1],
        [np.sqrt(3)/2, -1/2],
        [np.sqrt(3)/2, 1/2],
        [0, 1],
        [-np.sqrt(3)/2, 1/2],
        [-np.sqrt(3)/2, -1/2] 
    ])

    # transformations
    def rotateMatrix(a):
        return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])

    def translateVector(midpointx, midpointy):
        return np.array([[midpointx, midpointy]])

    def scaleVector(f):
        return np.array([[f, f]])

    # store list in this output file
    out_file = open(object_array_output_filename, 'w')

    obj_list = []

    for index, i in enumerate(file_data):
        data = i.split()                                           # split line of file into its 4 columns
        angle = float(data[1]) - 90                                # angle in second column, adjusted so cybot forward is 0, right is -90, left is 90
        width = float(data[3])                                     # width in fourth column
        distance = float((distance_info[index].split())[4])        # ping distance is more accurate, and stored in 5th parsed item of a distance info line

        # angle given is the start of the object, so quickly calculate angular width in degrees and compensate
        # if distance is 1 its a short object so this isnt needed
        if (distance != 1):
            angular_width = (width / distance) * 180/np.pi
            angle += angular_width/2

        # get the distance from the sensor in terms of units forward and right (right is flipped because of the coordinate system starting at the top left)
        sensor_forward = distance * np.cos(np.deg2rad(angle))
        sensor_right = -distance * np.sin(np.deg2rad(angle))

        # adjust to the midpoint of the cybot
        midpoint_forward = 10 + 3 * np.cos(np.deg2rad(angle))
        midpoint_right = -3 * np.sin(np.deg2rad(angle))

        sensor_forward += midpoint_forward
        sensor_right += midpoint_right

        # adjust to the midpoint of the object
        obj_midpoint_forward = (width/2) * np.cos(np.deg2rad(angle))
        obj_midpoint_right = (width/2) * np.sin(np.deg2rad(angle))

        sensor_forward += obj_midpoint_forward
        sensor_right += obj_midpoint_right

        # get vectors for the cameras forward and right directions
        cam_forward_x = np.sin(camera.yaw)
        cam_forward_y = -np.cos(camera.yaw)
        cam_right_x = np.cos(camera.yaw)
        cam_right_y = np.sin(camera.yaw)

        # first, scale to relative width of object. its centered around the origin, so scaling it by the radius will get us there.
        new_object = base_hexagon * scaleVector(width / 2)

        # second, rotate the object to its viewed angle according to camera direction while still about the origin
        new_object = new_object @ rotateMatrix(np.deg2rad(angle) + camera.yaw).T

        # third, translate the object to its viewed distance according to the camera position
        x_coord = camera.worldPos[0] + sensor_forward * cam_forward_x + sensor_right * cam_right_x
        z_coord = camera.worldPos[2] + sensor_forward * cam_forward_y + sensor_right * cam_right_y
        new_object = new_object + translateVector(x_coord, z_coord)

        # finally, write all vertices to the output file
        vertex_arr = new_object.tolist()

        obj_list.append(vertex_arr)

        # truncate floats and add facing and height fields, then print raw numbers to file
        for index, i in enumerate(vertex_arr):
            i[0] = float('%.2f' % i[0])
            i[1] = float('%.2f' % i[1])
            i.append(1)
            i.append(height)
            for j in range (4):
                out_file.write(str(i[j]) + " ")

    out_file.close()

    # for copying and pasting in desmos
    for o in (obj_list):
        for i in (o):
            print("(" + str(i[0]) + ", " + str(i[1]) + ")")
