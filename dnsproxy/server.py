#!/usr/bin/python

import shutil
import select
import socket
import sys
from dnslib import DNSRecord
from threading import Thread
from dnsproxy.config import Config
from dnsproxy.behavior import first_or_default, Behavior

BUFFER_SIZE = 1024
timeout = 10

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
        tcpSocket.listen(1)
        while self.active:
            conn, addr = tcpSocket.accept()
            data = conn.recv(BUFFER_SIZE)
            if not data:
                continue
            request = DNSRecord.parse(data)
            response = first_or_default(self.server.config.behaviors, request).handle(request)
            if response:
                tcpSocket.send(response.pack())
            conn.close()
        #tcpSocket.shutdown(1)
        tcpSocket.close()
        print 'TCP stopped'

    def stop(self):
        self.active = False

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
            if not rlist:
                continue
            data, addr = udpSocket.recvfrom(BUFFER_SIZE)
            request = DNSRecord.parse(data)
            response = first_or_default(self.server.config.behaviors, request).handle(request)
            if response:
                udpSocket.sendto(response.pack(), addr)
        #udpSocket.shutdown(1)
        udpSocket.close()
        print 'UDP stopped'

    def stop(self):
        self.active = False

class Server:
    def __init__(self, config = None):
        self.host = self.getNameservers()[0]
        if not config:
            config = Config()
        self.config = config
        self.udpThread = UdpThread(self)
        self.tcpThread = TcpThread(self)
        print 'DNS proxy server created'

    def is_alive(self):
        return self.udpThread.isAlive() or self.tcpThread.isAlive()

    def startUdp(self):
        if self.udpThread.isAlive():
            pass
        self.udpThread.start()

    def stopUdp(self):
        self.udpThread.stop()
        self.udpThread = UdpThread(self)

    def startTcp(self):
        if self.tcpThread.isAlive():
            pass
        self.tcpThread.start()

    def stopTcp(self):
        self.tcpThread.stop()
        self.tcpThread = TcpThread(self)

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
        try:
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.bind((self.host, self.config.dns_port))
        return udpSocket

    def createTcpSocket(self):
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpSocket.bind((self.host, self.config.dns_port))
        return tcpSocket

class DemoApp:
    """Interactive demo DNS proxy server app."""

    def __init__(self):
        self.config = Config()
        self.server = Server(self.config)

    def run(self):
        print 'Interactive demo DNS proxy server started.'
        print '(0 - exit; 1 - UDP on; 2 - UDP off; 3 - change action (default: 1))'
        while True:
            opt = int(raw_input('>>> Enter option number: '))
            print '--------------------'
            if opt == 0:
                self.server.stop()
                print 'Terminating program.'
                print ' ----- END -----'
                sys.exit()
            elif opt == 1:
                #self.server.startUdp()
                self.server.start()
            elif opt == 2:
                self.server.stopUdp()
            elif opt == 3:
                new_action = int(raw_input("> Enter action number: "))
                if new_action == 0:
                    self.config.behaviors = [Behavior('', 'block')]
                    print 'Action changed to 0 - blocking'
                elif new_action == 1:
                    self.config.behaviors = [Behavior('', 'forward')]
                    print 'Action changed to 1 - forwarding'
                elif new_action == 2:
                    self.config.behaviors = [Behavior('', 'respond', '192.168.1.50')]
                    print 'Action changed to 2 - spoofing (192.168.1.50)'
                else:
                    print 'Incorrect action number, only 0, 1 and 2 are allowed'
            else:
                print 'There is no option for given number.'

if __name__ == '__main__':
    app = DemoApp()
    app.run()
