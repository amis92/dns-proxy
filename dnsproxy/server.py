#!/usr/bin/python

import shutil
import select
import socket
import sys
from dnslib import DNSRecord
from threading import Thread
from dnsproxy.config import Config
from dnsproxy.behavior import first_or_default, Behavior
import logging

module_logger = logging.getLogger('dnsproxy.server')
BUFFER_SIZE = 1024
timeout = 10

class TcpThread(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.logger = logging.getLogger('dnsproxy.server.TcpThread')
        self.active = False
        self.server = server
        self.name = 'dnsproxy-TCP'
        self.logger.debug('created')

    def run(self):
        self.active = True
        self.logger.info('thread started')
        tcpSocket = self.server.createTcpSocket()
        tcpSocket.listen(1)
        while self.active:
            conn, addr = tcpSocket.accept()
            data = conn.recv(BUFFER_SIZE)
            if not data:
                continue
            request = DNSRecord.parse(data)
            self.logger.debug("handling request from '{addr}'".format(addr=addr))
            response = first_or_default(self.server.config.behaviors, request).handle(request)
            if response:
                tcpSocket.send(response.pack())
            conn.close()
        #tcpSocket.shutdown(1)
        tcpSocket.close()
        self.logger.info('thread stopped')

    def stop(self):
        self.active = False

class UdpThread(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.logger = logging.getLogger('dnsproxy.server.TcpThread')
        self.active = False
        self.server = server
        self.name = 'dnsproxy-UDP'
        self.logger.debug('created')

    def receive_and_handle(self, udpSocket):
        rlist, wlist, xlist = select.select([udpSocket], [], [], timeout)
        if not rlist:
            return
        data, addr = udpSocket.recvfrom(BUFFER_SIZE)
        request = DNSRecord.parse(data)
        self.logger.debug("handling request from '{addr}'".format(addr=addr))
        response = first_or_default(self.server.config.behaviors, request).handle(request)
        if response:
            udpSocket.sendto(response.pack(), addr)

    def run(self):
        self.active = True
        self.logger.info('thread started')
        udpSocket = self.server.createUdpSocket()
        try:
            while self.active:
                try:
                    self.receive_and_handle(udpSocket)
                except socket.error, err:
                    self.logger.exception('UDP handling threw exception')
                    if err.errno == socket.errno.WSAECONNRESET:
                        pass
                    else:
                        raise
        finally:
            self.server.stopUdp()
            #udpSocket.shutdown(1)
            udpSocket.close()
            self.logger.info('thread stopped')

    def stop(self):
        self.active = False

class Server:
    def __init__(self, config = None):
        self.logger = logging.getLogger('dnsproxy.server.Server')
        self.host = self.getNameservers()[0]
        if not config:
            config = Config()
        self.config = config
        self.udpThread = UdpThread(self)
        self.tcpThread = TcpThread(self)
        self.logger.debug('server created')

    def is_alive(self):
        tcp_alive = self.tcpThread.isAlive()
        udp_alive = self.udpThread.isAlive()
        self.logger.debug('polling alive status, tcp: {tcp}, udp: {udp}'.format(tcp=tcp_alive, udp=udp_alive))
        return tcp_alive or udp_alive

    def startUdp(self):
        self.logger.debug('trying to start UDP thread')
        if self.udpThread.isAlive():
            self.logger.debug('UDP thread already alive')
        self.udpThread.start()

    def stopUdp(self):
        self.logger.debug('trying to stop UDP thread')
        self.udpThread.stop()
        self.udpThread = UdpThread(self)

    def startTcp(self):
        self.logger.debug('trying to start TCP thread')
        if self.tcpThread.isAlive():
            self.logger.debug('TCP thread already alive')
        self.tcpThread.start()

    def stopTcp(self):
        self.logger.debug('trying to stop TCP thread')
        self.tcpThread.stop()
        self.tcpThread = TcpThread(self)

    def start(self):
        self.logger.debug('trying to start threads')
        self.startUdp()
        #self.startTcp()

    def stop(self):
        self.logger.debug('trying to stop threads')
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
            self.logger.debug('UDP sockopt setting failed', exc_info = True)
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.bind((self.host, self.config.dns_port))
        self.logger.debug('UDP socket bound to {host}:{port}'.format(host=self.host, port=self.config.dns_port))
        return udpSocket

    def createTcpSocket(self):
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            self.logger.debug('UDP sockopt setting failed', exc_info = True)
            udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcpSocket.bind((self.host, self.config.dns_port))
        self.logger.debug('TCP socket bound to {host}:{port}'.format(host=self.host, port=self.config.dns_port))
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
