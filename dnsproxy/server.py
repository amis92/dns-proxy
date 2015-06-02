#!/usr/bin/python

import select
import socket
import sys
from dnslib import *
import dns.exception
import dns.resolver

#read data from config file or read whole class Config
port = 53
BUFFER_SIZE = 1024
dnsHost = '5.226.79.90'
dnsPort = 53

timeout = 15

spoofedHost = '192.168.1.50'
action = 1
def getReaction(host):
  if (action == 0):
    rr = ReactionResponse(0, None)
  elif (action == 1):
    rr = ReactionResponse(1, None)
  elif (action == 2):
    rr = ReactionResponse(2, spoofedHost)
  else:
    rr = None
  return rr

class ReactionResponse:
  def __init__(self, code, reaction):
    self.code = code
    self.reaction = reaction

if __name__ == '__main__':
  print 'Server is running'
  
  udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  udpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
  udpSocket.bind(('',port))
  
  try:
    while 1:
      rlist, wlist, xlist = select.select([udpSocket], [], [], timeout)
      if rlist:

        data, addr = udpSocket.recvfrom(BUFFER_SIZE)
        request = DNSRecord.parse(data)
        qDomain = str(request.questions[0].qname)
        reaction = getReaction(qDomain)

        # 0 - block request
        if (reaction.code == 0):
          continue

        # 1 - forward request
        elif (reaction.code == 1):
          resolver = dns.resolver.Resolver()
          resolver.nameservers = [dnsHost]
          try:
            dnsQuery = resolver.query(qDomain, 'A')
          except dns.exception.DNSException:
            continue

          response = request.reply()
          for rdata in dnsQuery:
            ip = rdata.address
            response.add_answer(RR(qDomain, QTYPE.A, rdata=A(ip)))

          #print ">>>>>>>>>>>>>>response: "
          #print response
          udpSocket.sendto(response.pack(), addr)

        # 2 - spoof request
        elif (reaction.code == 2):
          response = request.reply()
          fIp = reaction.reaction
          response.add_answer(RR(qDomain, QTYPE.A, rdata=A(fIp)))

          #print ">>>>>>>>>>>>>>response: "
          #print response
          udpSocket.sendto(response.pack(), addr)

        else:
          print 'Error in ReactionResponse structure'
          sys.exit()

  except KeyboardInterrupt:
    print 'Server stopped, connection closed'
    udpSocket.close()
