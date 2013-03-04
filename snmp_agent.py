#!/usr/bin/python
import time
import bisect
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api

class SNMPAgent(object):
    def __init__(self, fakebras):
        print 'init'
        self._fakebras = fakebras
        self.create_mib_instr()
        self.start_agent()        
            
    def start_agent(self):
        print 'start_agent'
        try:
            transportDispatcher = AsynsockDispatcher()
            transportDispatcher.registerRecvCbFun(self.cbFun) #obrabotchik
            
            transportDispatcher.registerTransport(
                udp.domainName, udp.UdpSocketTransport().openServerMode(('localhost', 161))
            )
            
            transportDispatcher.jobStarted(1)
        except Exception as error:
            print 'error %s' % error

        try:
            # Dispatcher will never finish as job#1 never reaches zero
            transportDispatcher.runDispatcher()
        except:
            transportDispatcher.closeDispatcher()
            print 'error run disp'
            raise

    def cbFun(self, transportDispatcher, transportDomain, transportAddress, wholeMsg): #response
        print 'cbFun'
        while wholeMsg:
            msgVer = api.decodeMessageVersion(wholeMsg)
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                print('Unsupported SNMP version %s' % msgVer)
                return
            reqMsg, wholeMsg = decoder.decode(
                wholeMsg, asn1Spec=pMod.Message(),
                )
            rspMsg = pMod.apiMessage.getResponse(reqMsg)
            rspPDU = pMod.apiMessage.getPDU(rspMsg)        
            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            varBinds = []
            pendingErrors = []
            session_data = {}
            errorIndex = 0
            
            # 
            if reqPDU.isSameTypeWith(pMod.SetRequestPDU()):
                #parser
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    print oid
                    print val
                    if oid in self._mib_instr_idx:
                        session_data[self._mib_instr_idx[oid].title] = str(val)
                        varBinds.append((oid, self._mib_instr_idx[oid](msgVer)))
                    else:
                        # No such instance
                        varBinds.append((oid, val))
                        pendingErrors.append(
                            (pMod.apiPDU.setNoSuchInstanceError, errorIndex)
                            )
                        break
                
            else:
                # Report unsupported request type
                pMod.apiPDU.setErrorStatus(rspPDU, 'genErr')
            
            pMod.apiPDU.setVarBinds(rspPDU, varBinds)
            
            try:
                self._fakebras.stop_session(session_data, True)
            except Exception as error:
                raise

            # Commit possible error indices to response PDU
            for f, i in pendingErrors:
                f(rspPDU, i)
            
            transportDispatcher.sendMessage(
                encoder.encode(rspMsg), transportDomain, transportAddress
                )
        return wholeMsg

    def create_mib_instr(self):
        print 'create_mib_instr'
        try:
            mib_instr = (SessionId(), ActionKey())

            self._mib_instr_idx = {}
            for mib_var in mib_instr:
                self._mib_instr_idx[mib_var.name] = mib_var
        except Exception as error:
            print 'err: %s'%error
        
class SessionId(object):
    #name = (1,3,6,1,2,1,1,1,0)
    name = (1,3,6,1,4,1,2352,2,27,1,1,3,4,0)
    title = 'session_id'
    def __eq__(self, other): return self.name == other
    def __ne__(self, other): return self.name != other
    def __lt__(self, other): return self.name < other
    def __le__(self, other): return self.name <= other
    def __gt__(self, other): return self.name > other
    def __ge__(self, other): return self.name >= other
    def __call__(self, protoVer):
        return api.protoModules[protoVer].OctetString(
            'PySNMP example command responder SessionId'
            )
            
class ActionKey(object):
    #name = (1,3,6,1,2,1,1,1,0)
    name = (1,3,6,1,4,1,2352,2,27,1,1,3,9,0)
    title = 'action_key'
    def __eq__(self, other): return self.name == other
    def __ne__(self, other): return self.name != other
    def __lt__(self, other): return self.name < other
    def __le__(self, other): return self.name <= other
    def __gt__(self, other): return self.name > other
    def __ge__(self, other): return self.name >= other
    def __call__(self, protoVer):
        return api.protoModules[protoVer].OctetString(
            'PySNMP example command responder ActionKey'
            )
            
if __name__ == '__main__':
    print 'start'
    w = SNMPAgent()
