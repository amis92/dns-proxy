#!/usr/bin/python

import shutil
import select
import socket
import sys
from dnslib import DNSRecord
from threading import Thread
import dnsproxy.config
from dnsproxy.behavior import first_or_default

BUFFER_SIZE = 1024
timeout = 10
config = dnsproxy.config.Config()

# chyba trzeba wielowatkowosc dorobic tutaj, bo polaczenia sa za pomoca
# connect()
class TcpThread(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.active = False
        self.server = server
        self.name = 'dnsproxy TCP thread'

    def run(self):
        print 'TCP started'
        self.active = True
        tcpSocket = self.server.createTcpSocket()
        while self.active:
            tcpSocket.listen(1)
            conn, addr = s.accept()
            while True:
                data = conn.recv(BUFFER_SIZE)
                #if not data: break
                request = DNSRecord.parse(data)
            response = first_or_default(request, config.behaviors)
            if response:
                tcpSocket.send(response.pack())
            conn.close()

    def stop(self):
        self.active = False
        #tcpSocket.shutdown(1)
        if 'tcpSocket' in vars():
            tcpSocket.close()
        print 'TCP stopped'

class UdpThread(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.active = False
        self.server = server
        self.name = 'dnsproxy UDP thread'

    def run(self):
        print 'UDP started'
        self.active = True
        udpSocket = self.server.createUdpSocket()
        while self.active:
            rlist, wlist, xlist = select.select([udpSocket], [], [], timeout)
            if rlist:
                data, addr = udpSocket.recvfrom(BUFFER_SIZE)
                request = DNSRecord.parse(data)
                response = first_or_default(request, config.behaviors).handle(request)
                if response:
                    udpSocket.sendto(response.pack(), addr)

    def stop(self):
        self.active = False
        #udpSocket.shutdown(1)
        if 'udpSocket' in vars():
            udpSocket.close()
            print 'UDP stopped'

class Server:
    def __init__(self):
        self.resolverIP = self.getNameservers()[0]
        self.udpThread = UdpThread(self)
        self.tcpThread = TcpThread(self)
        print 'Server started'

    def startUdp(self):
        self.udpThread.start()

    def stopUdp(self):
        self.udpThread.stop()

    def startTcp(self):
        self.tcpThread.start()

    def stopTcp(self):
        self.tcpThread.stop()

    def start(self):
        self.startUdp()
        #self.startTcp()

    def stop(self):
        self.stopUdp()
        self.stopTcp()

    def getNameservers(self):
        try:
            with open('/etc/resolv.conf','r') as readFile:
                nameservers = [str(line.split(' ')[1].strip()) for line in readFile.readlines() if line.startswith('nameserver')]
        except Exception:
            return ['']
        return nameservers

    def createUdpSocket(self):
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udpSocket.bind((self.resolverIP, port))
        return udpSocket

    def createTcpSocket(self):
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        tcpSocket.bind((self.resolverIP, port))
        return tcpSocket

if __name__ == '__main__':
    print 'Program started'
    print '(0 - exit; 1 - UDP on; 2 - UDP off; 3 - change action (default: 1))'
    server = Server()
    while True:
        opt = int(raw_input('>>> Enter option number: '))
        print '--------------------'
        if opt == 0:
            server.stop()
            print 'Terminating program.'
            print ' ----- END -----'
            sys.exit()
        elif opt == 1:
            #server.startUdp()
            server.start()
        elif opt == 2:
            server.stopUdp()
        elif opt == 3:
            new_action = int(raw_input("> Enter action number: "))
            if new_action == 0:
                action = 0
                print 'Action changed to 0 - blocking'
            elif new_action == 1:
                action = 1
                print 'Action changed to 1 - forwarding'
            elif new_action == 2:
                action = 2
                print 'Action changed to 2 - spoofing (192.168.1.50)'
            else:
                print 'Incorrect action number, only 0, 1 and 2 are allowed'
        else:
            print 'There is no option for given number.'
