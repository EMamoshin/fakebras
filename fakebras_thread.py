#!/usr/bin/python

import sys
import random
import time
import threading
import simplejson
import base64
import M2Crypto
from snmp_agent import SNMPAgent

class ThreadFakeBrasStartWalledgarden(threading.Thread):
    """ Start walledgarden
    get new ip and change him state
    """
    def __init__(self, fakebras):
        self._fakebras = fakebras
        self._kill_received = False
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
    def run(self):
        self._fakebras._logger.add_log(self._fakebras._logger._debug, 
                                       'init thread')
        
        # Have our thread serve "forever"
        while not self._kill_received:
            # Get a client out of the queue
            try:
                # Get another IP from Queue
                current_ip = self._fakebras._pool.get()
                self._fakebras._logger.add_log(self._fakebras._logger._debug, '!!! ------------------------- CURRENT IP: %s'%current_ip)
                # Check IP
                if current_ip != None:
                    try:
                        data = self._fakebras._redis.get_data('ip', current_ip)
                        #opt82 = simplejson.dumps(data['opt32'])
                        # Session ID
                        data['session_id'] = self._fakebras.generate_session_id(current_ip)
                    except Exception as error:
                        except_text = 'Get IP data failed: %s' % error
                        self._fakebras._logger.add_log(self._fakebras._logger._error, except_text)
                        raise Exception(except_text)
                   
                    # First step - AccessReqeust
                    access_req_result = self._fakebras.send_radius_access_request(data)
                    
                    # if redis server responds, go to second step
                    if access_req_result != None and access_req_result == '1':
                        # rewrite row in table
                        # change policy
                        data['state'] = 2     
                        # Second step - AccounReqeust                          
                        self._fakebras.start_session(data, current_ip)
                        
                self._fakebras._pool.task_done()
            except Exception as error:
                self._fakebras._pool.task_done()
                except_text = "%s get %s exception" % (self.getName(), error)
                self._fakebras._logger.add_log(self._fakebras._logger._error, 
                                                           except_text)
                self._fakebras._pool.put(current_ip, block=False)
            
            time.sleep(0)
            
class ThreadFakeBrasSNMPAgent(threading.Thread):
    def __init__(self, fakebras):
        self._fakebras = fakebras
        self._kill_received = False
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
    def run(self):
        self._snmp_agent = SNMPAgent(self._fakebras)
        """
        # Have our thread serve "forever"
        while not self._kill_received:
            # Get a client out of the queue
            try:
                # Get another IP from Queue
                current_session_id = self._fakebras._stop_session_pool.get()
                
                # Check IP
                if current_ip != None:
                    self._fakebras.
                #self._fakebras._pool.task_done()
            except Exception as error:
                #self._fakebras._pool.task_done()
                except_text = "%s get %s exception" % (self.getName(), error)
                self._fakebras._logger.add_log(self._fakebras._logger._error, 
                                                           except_text)
                self._fakebras._pool.put(current_ip, block=False)
            
            time.sleep(0)
       """
