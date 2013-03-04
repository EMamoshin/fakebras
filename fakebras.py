#!/usr/bin/python

import sys
import random
import time
import threading
import Queue
import simplejson
import base64
import M2Crypto
#import M2Crypto
sys.path.append("/opt/redis_methods")
from redis_api import RedisMethods
from radius_client import BrasRadiusClient
from fakebras_thread import ThreadFakeBrasStartWalledgarden, ThreadFakeBrasSNMPAgent

class FakeBras(object):
    COUNT_POOLS = 3
    
    def __init__(self, logger_handler):
        self._logger = logger_handler
        self._threads_list = []
        
        try:
            self._redis = RedisMethods()
            self._bras_radius_client = BrasRadiusClient(self._logger,
                radius_domain='127.0.0.1', radius_secret='s3cr3t')
        except Exception as error:
            self._logger.add_log(self._logger._error, error)
            raise Exception(error)
            
        # Create our Queue:
        self._pool = Queue.Queue(self.COUNT_POOLS)
        #self._stop_session_pool = Queue.Queue(0)
        
        # Start 'change_state' threads
        self.start_threads('change_state')
        self.start_threads('snmp_agent')
    
    # IP with state: 0
    def check_ip_without_status(self):
        # Get all new IP
        self.get_new_ip()
        
        if self._new_ip_list:
            # Fill new Queue   
            for ip in self._new_ip_list:
                try:
                    self._pool.put(ip)
                    self._pool.join()
                except Exception, e:
                    pass
    # need create methods for work with session
    # session_start
    # session_stop
    # maybe access request
    def generate_session_id(self, ip):
        """ Generate new session id and write in DB
        """
        try:
            session_id = base64.b64encode(M2Crypto.m2.rand_bytes(16))
            session_id = session_id[:16]+'-'+session_id[16:]                       
            self._redis.set_value_in_ip(ip, 'session_id', session_id)
            return session_id
        except Exception as error:
            except_text = 'Failed generate session id: ' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text) 
    
    def start_session(self, data, current_ip):
        """ Start session
        1) send request on radius server
        """
        self._redis.update_data(current_ip, data)
        info_text = 'Change state to %s ' % (data['state']) +\
                    'for ip %s' % current_ip
        self._logger.add_log(self._logger._info, info_text)
        
        self.send_radius_accoun_request('Start', data)

    def stop_session(self, session_data={}, restart=False):
        """ Stop session by id
        1) remove key: 'sess_id' in BD
        2) send on radius server request
        """
        if session_data:
            session_id = session_data['session_id']
            action_key = session_data['action_key']
        else:
            except_text = 'Session Data is incorrect'
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
        try:
            data = self._redis.get_data('sessid', session_id)
            if data == None:
                except_text = 'Session ID not found!'
                self._logger.add_log(self._logger._error, except_text)
                raise Exception(except_text)
            # Remove info about session from BD
            self._redis.remove_key_from_ip_table(data['ip'], 'session_id')
            self._redis.remove_key_from_lookup('sessid', session_id)
            data['session_id'] = session_id
        except Exception as error:
            except_text = 'Get IP data failed: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
        
        self.send_radius_accoun_request('Stop', data)
        
        if restart == True:
            current_ip = data['ip']
            new_data = self._redis.get_data('ip', current_ip)
            new_data['session_id'] = self.generate_session_id(current_ip)
            naccess_result = self.send_radius_access_request(new_data)
            if naccess_result != None and naccess_result == '1':
                # rewrite row in table
                # change policy
                new_data['state'] = 1
                # Second step - AccounReqeust - First Session                          
                self.start_session(new_data, current_ip)
    
    def send_radius_access_request(self, data=None):
        """ Send AccessRequest to Radius Server
        """
        access_req_result = None
        access_req_data = {}
        try:
            # fill Access Request data object | delete comment later
            access_req_data['User-Name'] = data['mac']
            #access_req_data['Framed-IP-Address'] = current_ip
            #access_req_data['Agent-Circuit-Id'] = opt82['circuit_id']
            access_req_data['Acct-Session-Id'] = data['session_id']
        except Exception as error:
            except_text = 'Error: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
        
        # send package for first step
        try:
            access_req_result = self._bras_radius_client.\
                                send_request('AccessRequest', 
                                             access_req_data)
        except Exception as error:
            except_text = 'AccessRequest failed: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
        
        return access_req_result                              
    
    def send_radius_accoun_request(self, acct_type=None, data=None):
        """ Send AccountingRequest to Radius Server
        """
        if acct_type == None or data == None:
            except_text = 'Accounting Status Type or Data is incorrect.'
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
                   
        accoun_req_result = None
        accoun_req_data = {}
        
        accoun_req_data['Acct-Status-Type'] = acct_type
        accoun_req_data['User-Name'] = data['mac']
        #accoun_req_data['Mac-Addr'] = data['mac']
        #accoun_req_data['Agent-Circuit-Id'] = opt82['circuit_id']
        #accoun_req_data['Framed-IP-Address'] = current_ip
        #accoun_req_data['NAS-Port-Id'] = opt82['port_id']
        accoun_req_data['Acct-Session-Id'] = data['session_id'] 
        
        try:
            accoun_req_result = self._bras_radius_client.\
                                     send_request('AccountingRequest', 
                                                  accoun_req_data)
        except Exception as error:
            except_text = 'AccountingRequest failed: %s' % error
            self._logger.add_log(self._logger._error, except_text)
            raise Exception(except_text)
        
        if accoun_req_result != None and accoun_req_result == '3':
            info_text = 'Accounting request complete!'
            self._logger.add_log(self._logger._info, info_text)
    
    def get_new_ip(self):
        self._new_ip_list = self._redis.get_ip_by_state('0')
        
    def start_threads(self, option):
        # Start COUNT_POOLS threads for <ChangeState>:
        if option == 'change_state':
            for x in xrange(self.COUNT_POOLS):
                thread = ThreadFakeBrasStartWalledgarden(self)
                #self._threads_list.append(thread)
                thread.name = x
                thread.start()
        if option == 'snmp_agent':
            thread = ThreadFakeBrasSNMPAgent(self)
            #self._threads_list.append(thread)
            thread.name = option
            thread.start()
                
    def stop_threads(self):
        for thread in self._threads_list:
            thread._kill_received = True
        
