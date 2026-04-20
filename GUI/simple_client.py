# Author: Phillip Jones
# Modified: Noah Peterson, 12/11/2025
# Date: 10/30/2023
# Description: Client starter code that combines: 1) Simple GUI, 2) creation of a thread for
#              running the Client socket in parallel with the GUI, and 3) Simple recieven of mock sensor 
#              data for a server/cybot.for collecting data from the cybot.

import time # Time library   
import socket
import os  # import function for finding absolute path to this python script

##### START Define Functions  #########
# global flags, accessed by main
busy = False
bump = False
border = False
hole = False
dir = None
rx_message = bytearray(1) # Initialize a byte array

def send_forward():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "w"   # Update the message for the Client to send

def send_left():
        global gui_send_message 
        
        gui_send_message = "a"   

def send_right():
        global gui_send_message 
        
        gui_send_message = "d"   

def send_backwards():
        global gui_send_message 
        
        gui_send_message = "s"  

def send_stop():
        global gui_send_message 
        
        gui_send_message = "e"   

# Quit Button action.  Tells the client to send a Quit request to the Cybot, and exit the GUI
def send_quit():
        global gui_send_message 
        
        gui_send_message = "q"   
        time.sleep(1)

# sends a scan
def send_manual_scan():
        global gui_send_message 
        
        gui_send_message = "m"   

# receives 3 lines of mock object data for a bump, hole, or border event, so it can be used with the object generator
def receive_object_info():
        global cybot, rx_message, bump, border, hole
        print("Got a message from server: " + rx_message.decode() + "\n")
        if ("right" in rx_message.decode() or "left" in rx_message.decode()):
                rx_message = cybot.readline()          # receive command
                bump = False
                border = False
                hole = False
                return
        
        with open("./objects.txt", 'w') as obj_file:
                rx = cybot.readline().decode() # read header
                obj_file.write(rx) 
                print(rx)
                object_info = cybot.readline().decode() # read dummy info line (basically tells right or left)
                obj_file.write(object_info)
                print(object_info)
                rx = cybot.readline().decode() # read dummy distance
                obj_file.write(rx) 
                print(rx)

        rx_message = cybot.readline() # receive command
        return object_info

# manually read a line of input in case of synchronization issues
def read_line():
        global cybot
        print("Reading extra line: ")
        try:
                extra_line = cybot.readline().decode()
        except socket.timeout:
                restart_connection()
                return

        print(extra_line + "\n")
        return extra_line

# restarts the connection after a timeout
def restart_connection():
        global cybot, cybot_socket
        print("yo server bugged out twin im finna restart it")
        cybot.close()
        cybot_socket.close()
        print("aight i closed it im finna reopen it")
        HOST = "192.168.1.1" 
        PORT = 288
        cybot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cybot_socket.connect((HOST, PORT))
        cybot_socket.settimeout(4)           
        cybot = cybot_socket.makefile("rbw", buffering=0)
        print("aight you good twin go head and send another message: ")


## lots of sample code in here
# Client socket code (Run by a thread created in main)
def socket_thread():
        # Define Globals
        global gui_send_message   # Command that the GUI has requested be sent to the Cybot
        global cybot_socket
        global cybot
        # A little python magic to make it more convient for you to adjust where you want the data file to live
        # Link for more info: https://towardsthecloud.com/get-relative-path-python 
        absolute_path = os.path.dirname(__file__) # Absoult path to this python script
        relative_path = "./"   # Path to sensor data file relative to this python script (./ means data file is in the same directory as this python script)
        full_path = os.path.join(absolute_path, relative_path) # Full path to sensor data file
        filename = 'sensor-scan.txt' # Name of file you want to store sensor data from your sensor scan command
        objects_filename = 'objects.txt' # file to output scanned objects

        # Choose to create either a UART or TCP port socket to communicate with Cybot (Not both!!)
        # UART BEGIN
        #cybot = serial.Serial('COM100', 115200)  # UART (Make sure you are using the correct COM port and Baud rate!!)
        # UART END

        # TCP Socket BEGIN (See Echo Client example): https://realpython.com/python-sockets/#echo-client-and-server
        HOST = "192.168.1.1"  # The server's hostname or IP address
        PORT = 288        # The port used by the server
        cybot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        cybot_socket.connect((HOST, PORT))   # Connect to the socket  (Note: Server must first be running)
        cybot_socket.settimeout(4)
                      
        cybot = cybot_socket.makefile("rbw", buffering=0)  # makefile creates a file object out of a socket:  https://pythontic.com/modules/socket/makefile
        # TCP Socket END

        # Send some text: Either 1) Choose "Hello" or 2) have the user enter text to send
        send_message = "Hello"                            # 1) Hard code message to "Hello", or
        # send_message = input("Enter a message:") + '\n'   # 2) Have user enter text
        gui_send_message = "wait\n"  # Initialize GUI command message to wait 

        ## waits for first user input rather than an intial server echo so gui can easily be restarted
        print("send yo first command twin")
        while gui_send_message == "wait\n":
                time.sleep(0.001)

        cybot.write(send_message.encode())                               

        # Send messges to server until user sends "quit"
        while send_message != 'q':
                global busy
                global rx_message
                # Check if a sensor scan command has been sent
                if (send_message == "m"):
                        busy = True             # flag for gui

                        print("Requested Sensor scan from Cybot:\n")

                        # Create or overwrite existing sensor scan data file
                        file_object = open(full_path + filename,'w') # Open the file: file_object is just a variable for the file "handler" returned by open()
                        objects_file = open(full_path + objects_filename, 'w') #open objects file

                        write = False
                        obj_write = False
                        while (rx_message.decode().strip() != "END"): # Collect sensor data until "END" recieved
                                try:
                                        rx_message = cybot.readline()   # Wait for sensor response, readline expects message to end with "\n"
                                except socket.timeout:
                                        restart_connection()
                                        break
                                
                                ## variety of scan information indicators for logging to external files ##
                                if (rx_message.decode() == "Cleanes     IR Dist (cm)\n"):
                                        write = True

                                if (rx_message.decode() == "STOP\n"): # could close file in here too this shit is hacked together
                                        write = False

                                if (rx_message.decode() == "Object#    Angle    Distance    Width\n"):
                                        obj_write = True

                                if (rx_message.decode().strip() == "OBJEND"): # could close file in here dont gaf bout python optimization. had to strip because this one didnt work even though stop did
                                        obj_write = False
                                ## end ##

                                if (rx_message.decode().strip() != "END" and rx_message.decode().strip() != "STOP" and rx_message.decode().strip() != "OBJEND"):
                                        if (write):
                                                file_object.write(rx_message.decode())  # Write a line of sensor data to the file
                                        if (obj_write):
                                                objects_file.write(rx_message.decode()) # write to objects file
                                        print(rx_message.decode()) # Convert message from bytes to String (i.e., decode), then print
                                        
                        file_object.close() # Important to close file once you are done with it!!
                        objects_file.close()
                        busy = False

                else:   
                        global bump, border, hole, dir
                        busy = True             
                        print("Waiting for server reply\n")
                        try:
                                rx_message = cybot.readline()      # read control echo when control is sent/angle change when 'e' is sent
                        except socket.timeout:
                                restart_connection()
                                continue
                        
                        ## bump, hole, border events ##
                        if (rx_message.decode().strip() == "Hit left" or rx_message.strip() == "Hit right" or rx_message.decode().strip() == "Hit object dead on, sending object data."):
                                bump = True
                                dir = receive_object_info()
                        if (rx_message.decode().strip() == "There is a cliff on the left side! You are at the white border!" or rx_message.decode().strip() == "There is a cliff on the right side! You are at the white border!" or rx_message.decode().strip() == "There is a cliff in front! You are at the white border!"):
                                border = True
                                dir = receive_object_info()
                        if (rx_message.decode().strip() == "There is a hole on the left side! You are at the black border!" or rx_message.decode().strip() == "There is a hole on the right side! You are at the black border!" or rx_message.decode().strip() == "There is a hole in front! You are at the black border!"):
                                hole = True
                                dir = receive_object_info()
                        ## end ##
                        
                        busy = False
                        print("Got a message from server: " + rx_message.decode() + "\n") # Convert message from bytes to String (i.e., decode)


                # Choose either: 1) Idle wait, or 2) Request a periodic status update from the Cybot
                # 1) Idle wait: for gui_send_message to be updated by the GUI
                while gui_send_message == "wait\n": 
                        time.sleep(.001)  # Sleep for .1 seconds
                send_message = gui_send_message

                # 2) Request a periodic Status update from the Cybot:
                # every .1 seconds if GUI has not requested to send a new command
                #time.sleep(.1)
                #if(gui_send_message == "wait\n"):   # GUI has not requested a new command
                #        send_message = "status\n"   # Request a status update from the Cybot
                #else:
                #        send_message = gui_send_message  # GUI has requested a new command

                gui_send_message = "wait\n"  # Reset gui command message request to wait                        

                cybot.write(send_message.encode()) # Convert String to bytes (i.e., encode), and send data to the server
                
        print("Client exiting, and closing file descriptor, and/or network socket\n")
        cybot.write(send_message.encode()) #send quit to cybart
        time.sleep(2) # Sleep for 2 seconds
        cybot.close() # Close file object associated with the socket or UART
        cybot_socket.close()  # Close the socket (NOTE: comment out if using UART interface, only use for network socket option)

##### END Define Functions  #########

