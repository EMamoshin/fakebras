#!/usr/bin/python

from pyrad import dictionary, packet, server

class FakeServer(server.Server):
    def _HandleAuthPacket(self, pkt):
        server.Server._HandleAuthPacket(self, pkt)

        print "Received an authentication request"
        print "Attributes: "
        for attr in pkt.keys():
            print "%s: %s" % (attr, pkt[attr])
        print

        reply=self.CreateReplyPacket(pkt)

        reply.code=packet.AccessAccept

        self.SendReplyPacket(pkt.fd, reply)
    
    def _HandleAcctPacket(self, pkt):
        print 'start accn'
        server.Server._HandleAcctPacket(self, pkt)

        print "Received an accounting request"
        print "Attributes: "
        for attr in pkt.keys():
            print "%s: %s" % (attr, pkt[attr])
        print
     
        reply=self.CreateReplyPacket(pkt)
        self.SendReplyPacket(pkt.fd, reply)


srv=FakeServer(dict=dictionary.Dictionary("dicts/dictionary")) #
srv.hosts["127.0.0.1"]=server.RemoteHost("127.0.0.1", # 
    "s3cr3t", "localhost")
srv.BindToAddress("0.0.0.0") # 
srv.Run() #

