#!/usr/bin/python

import sys
import pyrad.packet as Packet #rename for easy reading
from pyrad.client import Client
from pyrad.dictionary import Dictionary

class BrasRadiusClient(object):
    """ """
    def __init__(self, logger=None, radius_domain=None, radius_secret=None):
        """ """
        self._logger = logger
        try:
            self._client = Client(server=radius_domain, secret=radius_secret,
                authport=1812, acctport=1813,
                dict=Dictionary('dicts/dictionary'))
        except Exception as error:
            except_text = 'Error when creating a Radius Client: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
        
    def send_request(self, code='AccessRequest', params={}):
        """ Sending AccessRequst. Attribute 'params' must be dictionary and 
        not null.
        """
        if not params or not isinstance(params, dict):
            except_text = 'Radius params incorrect or missing'
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
            
        try:
            if code == 'AccessRequest':
                packet_code = Packet.AccessRequest
                packet = self._client.CreateAuthPacket(code=packet_code)
            else:
                packet_code = Packet.AccountingRequest
                packet = self._client.CreateAcctPacket(code=packet_code)
        except Exception as error:
            except_text = 'Error when creating a Radius Packet: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)

        for key in params:
            packet[key] = params[key]

        try:
            return self.parse_reply(self._client.SendPacket(packet))
        except Exception as error:
            except_text = 'Error when sending packet[%s] ' % code+\
                          'on Radius Server: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
                    
    def parse_reply(self, reply=None):
        """ Test parser
        """
        if reply.code == Packet.AccessAccept:
            print "radius server response: access accepted".upper()
            return '1'
        elif reply.code == Packet.AccessReject:
            print "radius server response: access denied".upper()
            return '2'
        elif reply.code == Packet.AccountingResponse:
            print "radius server response: accounting response".upper()
            return '3'
        else:
            print "not found"
            return '999'
        
        print "Attributes returned by server:"
        for i in reply.keys():
            print "%s: %s" % (i, reply[i])
            
if __name__ == '__main__':
    fakeclient = BrasRadiusClient(radius_domain='127.0.0.1', 
        radius_secret='Kah3choteereethiejeimaeziecumi')
    
    req = {}
    req["User-Name"] = 'user'
    req["Framed-IP-Address"] = "1.1.1.1"
    req["Agent-Circuit-Id"] = "cid1"
    req["Acct-Session-Id"] = "48bf17ac"
    
    fakeclient.send_request(code='AccessRequest', params={'a': '1'})
    
