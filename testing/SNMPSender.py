# SNMP SET Command Generator
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time
import sys,os

class SNMPSender:
    lastResult = None
    pMod = api.protoModules[api.protoVersion2c]

    # Build PDU
    reqPDU = pMod.SetRequestPDU()

    def __init__(self, host='localhost', port=161, Log = None):
        self.host = host
        self.port = port
        if Log is None:
            self.Log = self.base_log
        else:
            self.Log = Log

    def base_log(self, level, req, msg):
        print msg
    
    def cbTimerFun(self, timeNow, startedAt=time()):
        if timeNow - startedAt > 10:
            raise Exception("Request timed out")
        
    def cbRecvFun(self,transportDispatcher, transportDomain, transportAddress, wholeMsg, reqPDU=None):
        result = []
        if reqPDU is None:
            reqPDU = self.reqPDU
        while wholeMsg:
            rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec = self.pMod.Message())
            rspPDU = self.pMod.apiMessage.getPDU(rspMsg)
            # Match response to request
            if self.pMod.apiPDU.getRequestID(reqPDU) == self.pMod.apiPDU.getRequestID(rspPDU):
                # Check for SNMP errors reported
                errorStatus = self.pMod.apiPDU.getErrorStatus(rspPDU)
                if errorStatus:
                    #make error processing
                    self.Log("WARN",None,"Error in SNMP communication: %s"%(errorStatus.prettyPrint()))
                else:
                    for oid, val in self.pMod.apiPDU.getVarBinds(rspPDU):
                        result.append([oid,val])
                        #print '%s = %s' (oid.prettyPrint(), val.prettyPrint())
                transportDispatcher.jobFinished(1)
        self.lastResult = result
        return wholeMsg

    def sendSNMPMessage(self, reqMsg):
        transportDispatcher = AsynsockDispatcher()
        
        transportDispatcher.registerTransport(udp.domainName, udp.UdpSocketTransport().openClientMode())
        transportDispatcher.registerRecvCbFun(self.cbRecvFun)
        transportDispatcher.registerTimerCbFun(self.cbTimerFun)
        
        transportDispatcher.sendMessage(encoder.encode(reqMsg), udp.domainName, (self.host, self.port))
        
        transportDispatcher.jobStarted(1)
        transportDispatcher.runDispatcher()
        transportDispatcher.closeDispatcher()

    def generateRequestID(self):
        res = str(int(time()))
        return res

    def sendMsg(self,sess_id,action_key):
        self.pMod.apiPDU.setDefaults(self.reqPDU)
        self.pMod.apiPDU.setRequestID(self.reqPDU,self.generateRequestID())
        self.pMod.apiPDU.setVarBinds(
            self.reqPDU,
            # A list of Var-Binds to SET
            #
            (
                (
                    (1,3,6,1,4,1,2352,2,27,1,1,3,9,0),
                    self.pMod.Gauge32(action_key)
                ),
                (
                    (1,3,6,1,4,1,2352,2,27,1,1,3,4,0), 
                    self.pMod.OctetString(sess_id)
                ),
            )
        )

        # Build message
        reqMsg = self.pMod.Message()
        self.pMod.apiMessage.setDefaults(reqMsg)
        #self.pMod.apiMessage.setCommunity(reqMsg, 'public')
        self.pMod.apiMessage.setCommunity(reqMsg, 'npm_community@wifi')
        self.pMod.apiMessage.setPDU(reqMsg, self.reqPDU)
        try:
          self.sendSNMPMessage(reqMsg)
        except Exception, e:
          print e
def SendSNMP(sess_id,action_key):
    print sess_id, action_key
    cmd = "python /opt/axess/Extensions/SNMPSender.py %s %s"%(sess_id,action_key)
    os.system(cmd)
    return
    #print '=========== Start SNMP'
    #t1 = time()
    #print t1
    #SNMPsenderObj = SNMPSender(host='172.26.203.21')
    SNMPsenderObj = SNMPSender()
    SNMPsenderObj.sendMsg(sess_id, action_key)
    #t2 = time()
    #print t2 - t1
    #print '==========='
    result = SNMPsenderObj.lastResult
    #del SNMPsenderObj
    return result
    
if __name__ == '__main__':
    if len(sys.argv) > 2:
        sess_id = sys.argv[1]
        action_key = int(sys.argv[2])
    else:
        sess_id = 'zkuOws7+3CBLjXqO-KGRvag=='
        action_key = 1
    #t1 = time()
    #print t1
    #SNMPsenderObj = SNMPSender(host='172.26.203.21')
    SNMPsenderObj = SNMPSender()
    SNMPsenderObj.sendMsg(sess_id, action_key)
    #t2 = time()
    #print t2 - t1
    print '==========='
    print SNMPsenderObj.lastResult
    print 
