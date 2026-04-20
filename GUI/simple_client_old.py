# Author: Phillip Jones
# Date: 10/30/2023
# Description: Client starter code that combines: 1) Simple GUI, 2) creation of a thread for
#              running the Client socket in parallel with the GUI, and 3) Simple recieven of mock sensor 
#              data for a server/cybot.for collecting data from the cybot.

# General Python tutorials (W3schools):  https://www.w3schools.com/python/

# Serial library:  https://pyserial.readthedocs.io/en/latest/shortintro.html 
#import serial
import time # Time library   
# Socket library:  https://realpython.com/python-sockets/  
# See: Background, Socket API Overview, and TCP Sockets  
import socket
import tkinter as tk # Tkinter GUI library
# Thread library: https://www.geeksforgeeks.org/how-to-use-thread-in-tkinter-python/
import threading
import os  # import function for finding absolute path to this python script
import numpy as np

##### START Define Functions  #########
busy = False
rx_message = bytearray(1) # Initialize a byte array

def send_forward():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "w"   # Update the message for the Client to send

def send_left():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "a"   # Update the message for the Client to send

def send_right():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "d"   # Update the message for the Client to send

def send_backwards():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "s"   # Update the message for the Client to send

def send_toggle():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "t"   # Update the message for the Client to send

def send_stop():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "e"   # Update the message for the Client to send

# Quit Button action.  Tells the client to send a Quit request to the Cybot, and exit the GUI
def send_quit():
        global gui_send_message # Command that the GUI has requested be sent to the Cybot
        
        gui_send_message = "q"   # Update the message for the Client to send
        time.sleep(1)


# Scan Button action.  Tells the client to send a scan request to the Cybot
def send_scan():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "h"   # Update the message for the Client to send

def send_manual_scan():
        global gui_send_message # Command that the GUI has requested sent to the Cybot
        
        gui_send_message = "m"   # Update the message for the Client to send



# Client socket code (Run by a thread created in main)
def socket_thread():
        # Define Globals
        global gui_send_message   # Command that the GUI has requested be sent to the Cybot

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
        HOST = "localhost"  # The server's hostname or IP address
        PORT = 8080        # The port used by the server
        cybot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        cybot_socket.connect((HOST, PORT))   # Connect to the socket  (Note: Server must first be running)
                      
        cybot = cybot_socket.makefile("rbw", buffering=0)  # makefile creates a file object out of a socket:  https://pythontic.com/modules/socket/makefile
        # TCP Socket END

        # Send some text: Either 1) Choose "Hello" or 2) have the user enter text to send
        send_message = "Hello"                            # 1) Hard code message to "Hello", or
        # send_message = input("Enter a message:") + '\n'   # 2) Have user enter text
        gui_send_message = "wait\n"  # Initialize GUI command message to wait                                

        cybot.write(send_message.encode()) # Convert String to bytes (i.e., encode), and send data to the server

        print("Sent to server: " + send_message) 

        # Send messges to server until user sends "quit"
        while send_message != 'q':
        
                # Check if a sensor scan command has been sent
                if (send_message == "H") or (send_message == "h") or (send_message == "m"):
                        global busy
                        global rx_message
                        busy = True

                        print("Requested Sensor scan from Cybot:\n")

                        # Create or overwrite existing sensor scan data file
                        file_object = open(full_path + filename,'w') # Open the file: file_object is just a variable for the file "handler" returned by open()
                        objects_file = open(full_path + objects_filename, 'w') #open objects file

                        write = False
                        obj_write = False
                        while (rx_message.decode() != "END\n"): # Collect sensor data until "END" recieved
                                rx_message = cybot.readline()   # Wait for sensor response, readline expects message to end with "\n"

                                if (rx_message.decode() == "Cleanes     IR Dist (cm)\n"):
                                        write = True

                                if (rx_message.decode() == "STOP\n"): # could close file in here too this shit is hacked together
                                        write = False

                                if (rx_message.decode() == "Object#    Angle    Distance    Width\n"):
                                        obj_write = True

                                if (rx_message.decode().strip() == "OBJEND"): # could close file in here dont gaf bout python optimization. had to strip because this one didnt work even though stop did
                                        obj_write = False

                                if (rx_message.decode() != "END\n" and rx_message.decode().strip() != "STOP" and rx_message.decode().strip() != "OBJEND"):
                                        if (write):
                                                file_object.write(rx_message.decode())  # Write a line of sensor data to the file
                                        if (obj_write):
                                                objects_file.write(rx_message.decode()) # write to objects file
                                        print(rx_message.decode()) # Convert message from bytes to String (i.e., decode), then print
                                        
                        file_object.close() # Important to close file once you are done with it!!
                        objects_file.close()
                        rx_message = cybot.readline()
                        print(rx_message.decode())

                        busy = False

                else:                
                        print("Waiting for server reply\n")
                        rx_message = cybot.readline()      # Wait for a message, readline expects message to end with "\n"
                        print("Got a message from server: " + rx_message.decode() + "\n") # Convert message from bytes to String (i.e., decode)


                # Choose either: 1) Idle wait, or 2) Request a periodic status update from the Cybot
                # 1) Idle wait: for gui_send_message to be updated by the GUI
                while gui_send_message == "wait\n": 
                        time.sleep(.1)  # Sleep for .1 seconds
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
socket_thread()
