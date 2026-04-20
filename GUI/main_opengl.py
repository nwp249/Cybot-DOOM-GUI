# Source: https://github.com/jordansavant/doomengine.python
# Modified: Noah Peterson, 12/11/2025

import pygame, engine_opengl, math, os
from engine_opengl.eventlistener import EventListener
from engine_opengl.linedef import LineDef
from engine_opengl.solidbspnode import SolidBSPNode
from engine_opengl.camera import Camera
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import time
import simple_client
import threading
from object_generator import generate_objects
import numpy as np

# MAP ROOMS
# Lines, each vertex connects to the next one in CW fashion
# third element is direction its facing, when CW facing 1 = left
polygons = [
    #room
    [
        # x, z, facing, height (y)
        [30,  30, 0, 10],
        [1006, 30, 0, 10],
        [1006, 1006, 0, 10],
        [30, 1006, 0, 10]
    ],
]

# Global variables
absolute_path = os.path.dirname(__file__)
allLineDefs = []
solidBsp = None
screen = None
listener = None
camera = None
font = None
mode = 0
max_modes = 4
collisionDetection = True
fullscreen = False
displayWidth = 0
displayHeight = 0
resolutionWidth = 0
resolutionHeight = 0
targetWidth = 1280
targetHeight = 720
timer = 0
actualTime = 0
FPS = 60
dt = int(1 / FPS * 1000)
yaw = 0
oldYaw = 0
currDegree = 0
camPos = [0, 0]
oldCamPos = [0,0]
currPos = [0,0]

## creates the bsp tree because this a doom engine (didn't write this)
# Create SolidBSP for Level
def createBSP():
    global allLineDefs
    for i, v in enumerate(polygons):
        polygon = polygons[i]
        lineDefs = []
        for idx, val in enumerate(polygon):
            lineDef = LineDef()

            # first point, connect to second point
            if idx == 0:
                lineDef.asRoot(polygon[idx][0], polygon[idx][1], polygon[idx + 1][0], polygon[idx + 1][1], polygon[idx + 1][2], polygon[idx + 1][3])
                lineDefs.append(lineDef)
                allLineDefs.append(lineDef)

            # some point in the middle
            elif idx < len(polygon) - 1:
                lineDef.asChild(lineDefs[-1], polygon[idx + 1][0], polygon[idx + 1][1], polygon[idx + 1][2], polygon[idx + 1][3])
                lineDefs.append(lineDef)
                allLineDefs.append(lineDef)

            # final point, final line, connects back to first point
            elif idx == len(polygon) - 1:
                lineDef.asLeaf(lineDefs[-1], lineDefs[0], polygon[idx][2], polygon[idx][3])
                lineDefs.append(lineDef)
                allLineDefs.append(lineDef)

## map modes (didn't write this)
def mode_up():
    global mode
    mode = (mode + 1) % max_modes

def mode_down():
    global mode
    mode = (mode - 1) % max_modes

## sends scan to cybot
def on_m():
    global solidBsp, camera
    
    simple_client.send_manual_scan()
    time.sleep(1)

    while(simple_client.busy): ## rudimentary blocking
        time.sleep(0.1)

    print("gofuckyourselfagain")

    generate_objects(camera, 10)
    render_new_objects()

## fullscreens the game (not mine)
def on_f():
    global fullscreen, screen, displayWidth, displayHeight
    global resolutionWidth, resolutionHeight, targetWidth, targetHeight
    fullscreen = not fullscreen
    # get world model matrix
    m = glGetDoublev(GL_MODELVIEW_MATRIX).flatten()
    if fullscreen:
        displayWidth, displayHeight = resolutionWidth, resolutionHeight
        screen = pygame.display.set_mode((displayWidth,displayHeight), DOUBLEBUF|OPENGL|FULLSCREEN)
    else:
        displayWidth, displayHeight = targetWidth, targetHeight
        screen = pygame.display.set_mode((displayWidth,displayHeight), DOUBLEBUF|OPENGL)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    # reapply window matrix
    glLoadMatrixf(m)

## sends quit
def on_q():
    global screen, won
    simple_client.send_quit()
    time.sleep(0.01)
    won = True

### movement controls ###

def on_w():
    save_game_state()
    simple_client.send_forward()
    time.sleep(0.01)
    while(simple_client.busy):
        checkStatus()

def on_a():
    save_game_state()
    simple_client.send_left()
    time.sleep(0.01)
    while(simple_client.busy):
        checkStatus()

def on_s():
    save_game_state()
    simple_client.send_backwards()
    time.sleep(0.01)
    while(simple_client.busy):
        checkStatus()

def on_d():
    save_game_state()
    simple_client.send_right()
    time.sleep(0.01)
    while(simple_client.busy):
        checkStatus()
        
### end ###

## checks flags in client for bump, hole, or border events
def checkStatus():
    if (simple_client.bump or simple_client.border or simple_client.hole):
        if (simple_client.bump):
            simple_client.bump = False
            addShortObject()
        if (simple_client.border):
            simple_client.border = False
            addBorder()
        if (simple_client.hole):
            simple_client.hole = False
            addHole()

## adds a short point signifying a hole
def addHole():
    global camera
    print("Hole!!")
    generate_objects(camera, 1)
    render_new_objects()
    
## adds a tall point signifying a border
def addBorder():
    global camera
    print("Border!!")
    generate_objects(camera, 10)
    render_new_objects()

## adds a short object
def addShortObject():
    print("Short object!!")
    global camera
    generate_objects(camera, 2)
    render_new_objects()

## gets current camera state
def get_old_info():
    global yaw, oldYaw, camPos, oldCamPos, camera
    oldYaw = camera.yaw
    oldCamPos[0] = camera.worldPos[0]
    oldCamPos[1] = camera.worldPos[2]

## writes camera position and walls to a file in case of emergency
def save_game_state():
    global camera, polygons
    get_old_info()
    with open('./game-state.txt', 'w') as f:
        lines = [str(polygons), "\n", str(camera.worldPos)]
        f.writelines(lines)

## this doesn't work because trying to move the walls somehow removed the reference to the event listener
## so i removed that part and didnt use this
def shift_everything(dir):
    global camera, polygons, oldCamPos, allLineDefs, solidBsp
    get_old_info()
    x_shift = 0
    z_shift = 0
    match dir:
        case pygame.K_UP:
            z_shift = 5
        case pygame.K_DOWN:
            z_shift = -5
        case pygame.K_LEFT:
            x_shift = -5
        case pygame.K_RIGHT:
            x_shift = 5
    for p in polygons:
        for point in p:
            point[0] += x_shift
            point[1] += z_shift

    camera.setPosition(x_shift, 0, x_shift)
    camera.update()

## this gets called after every movement command to adjust the game camera position according to roomba wheel data (not very accurate)
def on_up():
    global yaw, oldYaw, currDegree, camPos, oldCamPos, currPos, camera
    
    simple_client.send_stop()
    time.sleep(0.01)

    while(simple_client.busy):
        time.sleep(0.001)

    ## does this count as thread safety im really not sure what that term means
    try:
        cybot_val = float(simple_client.rx_message)
    except ValueError:
        print("ah hell nah yo threads busted 💀💀💀")
        var = simple_client.read_line()
        try:                                    ## try one more time because the bump sensors mess with the syncing a lot and the value the camera needs to adjust by is usually on the next line
            cybot_val = float(var)
            print("good recovery it was on the next one")
        except ValueError:
            print("im crine i cant even find it")
            return


    ## correct turning errors with real data (currently an estimate from roomba motors, can easily adapt to be precise gyroscope data)
    yaw = camera.yaw
    if (yaw != oldYaw):
        turn_degrees_real = cybot_val
        
        print("Camera yaw change:")
        print(np.rad2deg(yaw) - np.rad2deg(oldYaw))

        print("Real change: ")
        print(-turn_degrees_real)
        currDegree += turn_degrees_real ## stores the roomba's "yaw"

        print("Current yaw:")
        print(np.rad2deg(yaw))

        print("Current roomba deg:")
        print(-currDegree)

        print("Expected jump (positive is cw):")
        print(-((np.rad2deg(yaw) - np.rad2deg(oldYaw)) + turn_degrees_real))

        ## roomba has left turns as positive. setYaw sets the yawDelta to the difference between the yaw change and actual position change, then we force an update. 
        ## if speeds are decently synced the jump shouldnt be too bad
        ## setting the yaw directly doesn't work right so it had to be complicated like this
        camera.setYawDeg(-((np.rad2deg(yaw) - np.rad2deg(oldYaw)) + turn_degrees_real)) 
        camera.update()

        ## update camera stuff
        oldYaw = camera.yaw
        print("Updated yaw:")
        print(np.rad2deg(camera.yaw))
        print()
        print("Enter next command: ")

    ## TODO:  maybe collect data to dynamically adapt the camera speed to match turning/movement of the cybart

    ## this section handles forward/backward error correction which i think worked pretty well
    camPos[0] = camera.worldPos[0]
    camPos[1] = camera.worldPos[2]
    if (math.fabs(camPos[0] - oldCamPos[0]) > 4  or math.fabs(camPos[1] - oldCamPos[1]) > 4):
        movement_real = cybot_val

        print("Camera position change: ")
        print(str(camPos[0] - oldCamPos[0]) + ", " + str(camPos[1] - oldCamPos[1]))

        camera_change = math.sqrt(((camPos[0] - oldCamPos[0]) ** 2 + (camPos[1] - oldCamPos[1]) ** 2))
        print(camera_change)

        print("Real change: ")
        print(movement_real)

        ## camera movement forward and right
        movement_real_x = movement_real * np.sin(camera.yaw)
        print(movement_real_x)
        movement_real_z = -movement_real * np.cos(camera.yaw)
        print(movement_real_z)

        print("Old pos: " + str(oldCamPos))

        ## calculate new coordinates
        x_coord = oldCamPos[0] + movement_real_x 
        z_coord = oldCamPos[1] + movement_real_z
        print(x_coord)
        print(z_coord)

        print("Expected jump: ")
        jump = math.sqrt(((x_coord - camPos[0]) ** 2 + (z_coord - camPos[1]) ** 2))
        print(jump)

        ## update camera stuff
        camera.setPosition(x_coord - camPos[0], 0, z_coord - camPos[1])
        camera.update()
        oldCamPos[0] = camera.worldPos[0]
        oldCamPos[1] = camera.worldPos[2]  
        print()
        print("Enter next command: ") 

## places a point right in front of the camera
def make_thing_where_you_think_thing_is():
    global camera
    lines = ["Object#    Angle    Distance    Width\n", "1          90       1   2\n", "Object 1 PING distance: 1" ] 
    with open('./objects.txt', 'w') as f:
        f.writelines(lines)
    generate_objects(camera, 2)
    render_new_objects()

## renders new objects into the game from the object defs file
def render_new_objects():
    global solidBsp, allLineDefs

    with open('./object-defs.txt') as f:
        lines = f.read().split()

    if (lines[0] == "None"):
        return

    ## parses values back into 3d array and appends it to the polygons list
    rows = 6
    cols = 4
    depth = int(len(lines) / rows / cols)
    curr = 0
    for i in range (depth):
        objs = []
        for j in range (rows):
            points = []
            for k in range (cols):
                if (k < 2):
                    points.append(float(lines[curr]))
                else:
                    points.append(int(lines[curr]))
                curr += 1
            objs.append(points)
        print(objs)
        polygons.append(objs)

    ## redraw map
    allLineDefs.clear()
    createBSP()
    solidBsp = SolidBSPNode(allLineDefs)
    draw()

### opengl stuff i didn't write, draws minimap ###
def drawLine(start, end, width, r, g, b, a):
    glLineWidth(width)
    glColor4f(r, g, b, a)
    glBegin(GL_LINES)
    glVertex2f(start[0], start[1])
    glVertex2f(end[0], end[1])
    glEnd()

def drawPoint(pos, radius, r, g, b, a):
    glColor4f(r, g, b, a)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(pos[0], pos[1]);
    for angle in range(10, 3610, 2):
        angle = angle / 10
        x2 = pos[0] + math.sin(angle) * radius;
        y2 = pos[1] + math.cos(angle) * radius;
        glVertex2f(x2, y2);
    glEnd()

### end ###

## opengl thing i did write to make the bumper on the cybot in the minimap ###
def drawSemi(pos, radius, offset, r, g, b, a):
    glColor4f(r, g, b, a)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(pos[0], pos[1])
    for angle in range(int(((np.pi)/2 * 100) + offset * -100), int(((np.pi * 3/2) * 100) + offset * -100), 2):
        angle = angle / 100
        glVertex2f(pos[0] + math.sin(angle) * radius, pos[1] + math.cos(angle) * radius)
    glEnd()



###### Below here is mostly game engine stuff I didn't write, but I commented on what I modified using 2 hashes ######


def drawHud(offsetX, offsetY, width, height, mode, camera, allLineDefs, walls):
    # wall lines
    if mode == 0:
        for lineDef in allLineDefs:
            # draw wall
            mapStart = [lineDef.start[0] + offsetX, lineDef.start[1] + offsetY]
            mapEnd = [lineDef.end[0] + offsetX, lineDef.end[1] + offsetY]
            drawLine(mapStart, mapEnd, 1, 0.0, 0.0, 1.0, 1.0)
            # draw facing dir
            ln = 7
            mx = lineDef.mid[0]
            my = lineDef.mid[1]
            nx = lineDef.normals[lineDef.facing][0] * ln
            ny = lineDef.normals[lineDef.facing][1] * ln
            if lineDef.facing == 1:
                drawLine([mx + offsetX, my + offsetY], [mx + nx + offsetX, my + ny + offsetY], 2, 0.0, 1.0, 1.0, 1.0)
            else:
                drawLine([mx + offsetX, my + offsetY], [mx + nx + offsetX, my + ny + offsetY], 2, 1.0, 0.0, 1.0, 1.0)
    if mode == 1:
        solidBsp.drawSegs(drawLine, offsetX, offsetY)
    if mode == 2:
        solidBsp.drawFaces(drawLine, camera.worldPos[0], camera.worldPos[2], offsetX, offsetY)
    if mode == 3:
        for wall in walls:
            start = [wall.start[0] + offsetX, wall.start[1] + offsetY];
            end = [wall.end[0] + offsetX, wall.end[1] + offsetY];
            drawLine(start, end, 1, 0, .3, 1, 1)

    # camera
    angleLength = 10
    camOrigin = [camera.worldPos[0] + offsetX, camera.worldPos[2] + offsetY]
    camNeedle = [camOrigin[0] + math.cos(camera.yaw - math.pi/2) * angleLength, camOrigin[1] + math.sin(camera.yaw - math.pi/2) * angleLength]
    drawLine(camOrigin, camNeedle, 1, 1, .5, 1, 1)
    drawPoint(camOrigin, 32.99/2, 1, 1, 1, 1)                       ## the game is scaled to 1cm -> 1 unit (pixels?)
    drawSemi(camOrigin, 34.85/2, camera.yaw, .55, .55, .55, 1)      ## draws the cybot bumper 

    # render crosshair
    drawLine([displayWidth/2, displayHeight/2 - 8], [displayWidth/2, displayHeight/2 - 2], 2, 1, .3, .3, 1)
    drawLine([displayWidth/2, displayHeight/2 + 2], [displayWidth/2, displayHeight/2 + 8], 2, 1, .3, .3, 1)
    drawLine([displayWidth/2 - 8, displayHeight/2], [displayWidth/2 - 2, displayHeight/2], 2, 1, .3, .3, 1)
    drawLine([displayWidth/2 + 2, displayHeight/2], [displayWidth/2 + 8, displayHeight/2], 2, 1, .3, .3, 1)

    # collision flag dot
    if camera.collisionDetection:
        drawPoint([displayWidth - 50, 50], 10, 0, 1, 0, 1)
    else:
        drawPoint([displayWidth - 50, 50], 10, 1, 0, 0, 1)


def drawWalls(walls, camera):
    for i, wall in enumerate(walls):
        glBegin(GL_QUADS)
        c = wall.drawColor
        glColor3f(c[0]/255, c[1]/255, c[2]/255)
        glVertex3f(wall.start[0],   0,              wall.start[1])
        glVertex3f(wall.start[0],   wall.height,    wall.start[1])
        glVertex3f(wall.end[0],     wall.height,    wall.end[1])
        glVertex3f(wall.end[0],     0,              wall.end[1])
        glEnd()


def update():
    listener.update()
    camera.update()
    if (simple_client.bump or simple_client.border or simple_client.hole):  ## this was an attempt to get the camera to stop moving when the cybot does. it doesn't work
        listener.keyHolds[pygame.K_w] = False


def draw():
    # sort walls around camera x and z
    walls = []
    solidBsp.getWallsSorted(camera.worldPos[0], camera.worldPos[2], walls)

    # RENDER 3D
    glPushMatrix()

    # projection
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, displayWidth, displayHeight)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (displayWidth/displayHeight), 0.00001, 5000)
    # models
    glMatrixMode(GL_MODELVIEW)

    drawWalls(walls, camera)

    glPopMatrix()
    # END 3D

    # RENDER 2D
    glPushMatrix()

    # projection
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, displayWidth, displayHeight, 0.0)
    # models
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    drawHud(20, 20, 400, 300, mode, camera, allLineDefs, walls)

    glPopMatrix()
    # END 2D

    ## victory screen ##
    if won:
        screen = pygame.display.set_mode((displayWidth, displayHeight))
        screen.blit(img, (0,0))

    # update display
    pygame.display.flip()


def initialize():
    """Initialize all game systems"""
    global solidBsp, screen, listener, camera, font, img, won  ## img and won are for victory screen
    global displayWidth, displayHeight, resolutionWidth, resolutionHeight
    global targetWidth, targetHeight, actualTime
    
    # Create BSP
    createBSP()
    solidBsp = SolidBSPNode(allLineDefs)
    print(solidBsp.toText(), flush=True)

    # GAME SETUP
    pygame.init()

    # get os resolution
    displayInfo = pygame.display.Info()
    resolutionWidth = displayInfo.current_w
    resolutionHeight = displayInfo.current_h

    # start with this resolution in windowed
    displayWidth = targetWidth
    displayHeight = targetHeight

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode((displayWidth, displayHeight), DOUBLEBUF|OPENGL)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    font = pygame.font.Font(None, 36)
    listener = EventListener()
    camera = Camera(solidBsp)

    ## victory screen
    relative_path = "./assets/success.jpg" 
    full_path = os.path.join(absolute_path, relative_path)
    img = pygame.image.load(full_path).convert()
    won = False

    # set base camera application for matrix
    glMatrixMode(GL_MODELVIEW)
    camera.setPosition(503, 2, 403)
    camera.setYaw(0)

    ## initialize my camera position references, this doesn't work for whatever reason
    oldCamPos[0] = camera.worldPos[0] 
    oldCamPos[1] = camera.worldPos[2]
    camPos[0] = camera.worldPos[0]
    camPos[1] = camera.worldPos[2]

    # Setup event listeners
    ## i obviously modified most of these
    listener.onKeyUp(pygame.K_m, on_m)
    listener.onKeyUp(pygame.K_f, on_f)
    listener.onKeyHold(pygame.K_a, camera.rotateLeft)
    listener.onKeyHold(pygame.K_d, camera.rotateRight)
    listener.onKeyHold(pygame.K_w, camera.moveForward)
    listener.onKeyHold(pygame.K_s, camera.moveBackward)
    listener.onKeyDown(pygame.K_w, on_w)
    listener.onKeyUp(pygame.K_w, on_up)
    listener.onKeyDown(pygame.K_a, on_a)
    listener.onKeyUp(pygame.K_a, on_up)
    listener.onKeyDown(pygame.K_s, on_s)
    listener.onKeyUp(pygame.K_s, on_up)
    listener.onKeyDown(pygame.K_d, on_d)
    listener.onKeyUp(pygame.K_d, on_up)
    listener.onKeyUp(pygame.K_p, on_q)
    listener.onKeyUp(pygame.K_r, simple_client.read_line)
    listener.onKeyUp(pygame.K_l, save_game_state)
    listener.onKeyUp(pygame.K_i, make_thing_where_you_think_thing_is)


    # info
    ## includes my functions
    print("f (fullscreen)")
    print("up_arrow (map mode up)")
    print("down_arrow (map mode down)")
    print("m (scan)")
    print("q (quit)")
    print("l (save game)")
    print("i (insert point)")
    print("r (read line from server)")
    print("wasd (movement)\n", flush=True)
    
    actualTime = pygame.time.get_ticks()


def main_loop():
    """Main game loop"""
    global timer, actualTime, won
    
    updateCounter = 0
    drawCounter = 0
    
    while True:
        # UPDATE at fixed intervals
        newTime = pygame.time.get_ticks()
        frameTime = newTime - actualTime
        if frameTime > 250:
            frameTime = 250  # avoid spiral of death
        timer += frameTime
        while timer >= dt:
            try:                ## the win screen blows it up so I catch exceptions
                update()
            except OpenGL.error.GLError:
                break
            updateCounter += 1
            timer -= dt
        try:
            draw()
            drawCounter += 1
        except:
            pass

        actualTime = newTime

## main declaration, this was originally just an unorganized script
if __name__ == "__main__":
    initialize()
    socket_thread = threading.Thread(target=simple_client.socket_thread) # Create the thread
    socket_thread.start() # Start the thread
    main_loop()