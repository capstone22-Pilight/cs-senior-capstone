# Sample program to cycle the lights on the ESP module
# Make sure the ESP is configured before running
import socket
import time

# Default socket and IP for the module
# The port is not flexible, but the IP can
# be configured via a serial connection.
# It can also accept an IP from the 
# broadcast.py program
TCP_IP = '192.168.4.1'
TCP_PORT = 9999

# Base command, see datasheet for details on
# what you want to use, but we'll loop through
# all the options
CMD = '0000'
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

s.connect((TCP_IP, TCP_PORT))

# The relay has each block represent part of the 
# command string, so for instance the command 0001
# will turn relays 0, 1, and 2 off and 3 on, and the 
# command 0110 will turn on 1 and 2 and turn off 0 and 3
for x in range(0,15):
	CMD = '{:0{}b}'.format(long(CMD,2) + 1,len(CMD))
	print "Sending: ", CMD
	s.send(CMD)
	time.sleep(1)

# Close the socket in the end
s.close()


