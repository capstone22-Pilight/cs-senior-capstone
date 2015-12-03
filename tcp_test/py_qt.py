from PyQt4 import QtGui, QtCore

class Window(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
 	self.resize(320, 240)
        self.button = QtGui.QPushButton('Test', self)
        self.button.clicked.connect(self.handleButton)
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.button)

    def handleButton(self):
        import socket
        import time

        TCP_IP = '192.168.4.1'
        TCP_PORT = 9999
        CMD = '0000'
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
       
        for x in range(0,15):
	        CMD = '{:0{}b}'.format(long(CMD,2) + 1,len(CMD))
	        print "Sending: ", CMD
	        s.send(CMD)
	        time.sleep(1)	 
	
	s.close()

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
