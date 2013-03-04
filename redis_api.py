#!/usr/bin/python

import redis
import sys
import random
sys.path.append("/opt/redis_methods/")

class RedisMethods(object):
    """
    self._field_name_lookup_mac = 'lookup:mac'
    self._field_name_lookup_opt82 = 'lookup:opt82'
    self._field_name_ip = 'ip'
    self._field_name_ip = 'state'
    """

    def __init__(self):
        self._rh = redis.StrictRedis(host='localhost', port=6379, db=0)

    def create_ip(self, ip_data):
        """ Create an item in Redis """
        ip = ip_data['ip']
        del ip_data['ip']
        if 'state' in ip_data:
            ip_data['state'] = '0'
        pipe = self._rh.pipeline()
        try:
            pipe.hmset('ip:%s' % ip, ip_data)

            pipe.hset('ip:lookup:mac', ip_data['mac'], ip)
            pipe.hset('ip:lookup:opt82', ip_data['opt82'], ip)

            pipe.sadd('ip:state:0', ip)
            pipe.execute()
        except Exception, e:
            return 'Error: %s' % e

    def remove_ip(self, ip):
        """ Delete item from Redis """
        pipe = self._rh.pipeline()
        try:
            pipe.watch('ip:%s' % ip)
            mac = pipe.hget('ip:%s' % ip, 'mac')
            opt82 = pipe.hget('ip:%s' % ip, 'opt82')
            state = pipe.hget('ip:%s' % ip, 'state')
            
            pipe.multi()
            pipe.delete('ip:%s' % ip)
            pipe.hdel('ip:lookup:mac', mac)
            pipe.hdel('ip:lookup:opt82', opt82)
            pipe.srem('ip:state:%s' % state, ip)
            pipe.execute()
        except Exception, e:
            return 'Error: %s' % e
        
    def get_data(self, item, value):
        """ Get IP info by IP or MAC or OPT82 """
        try:
            if item == 'ip':
                result = self._rh.hgetall('ip:%s' % value)
            elif item == 'mac':
                item_ip = self._rh.hget('ip:lookup:mac', value)
                result['ip'] = item_ip
                result = self._rh.hgetall('ip:%s' % item_ip)
            elif item == 'opt82':
                item_ip = self._rh.hget('ip:lookup:opt82', value)
                result['ip'] = item_ip
                result = self._rh.hgetall('ip:%s' % item_ip)
            elif item == 'sessid':
                result = {}
                item_ip = self._rh.hget('ip:lookup:sessid', value)
                if item_ip == None:
                    return None
                result = self._rh.hgetall('ip:%s' % item_ip)
                result['ip'] = item_ip
        except Exception, e:
            return 'Error: %s' % e
        
        return result
        
    def update_data(self, ip, new_data):
        """ Update IP info """
        pipe = self._rh.pipeline() 
        try:
            pipe.watch('ip:%s' % ip)
            mac = pipe.hget('ip:%s' % ip, 'mac')
            opt82 = pipe.hget('ip:%s' % ip, 'opt82')
            state = pipe.hget('ip:%s' % ip, 'state')
            
            pipe.multi()
            pipe.hmset('ip:%s' % ip, new_data)
            
            pipe.hdel('ip:lookup:mac', mac)
            pipe.hdel('ip:lookup:opt82', opt82)
            pipe.hset('ip:lookup:mac', new_data['mac'], ip)
            pipe.hset('ip:lookup:opt82', new_data['opt82'], ip)

            pipe.srem('ip:state:%s' % state, ip)
            pipe.sadd('ip:state:%s' % new_data['state'], ip)
            pipe.execute()
        except Exception, e:
            return 'Error: %s' % e
            
    def get_ip_by_state(self, state):
        """ Get IP by state """
        try:
            result = self._rh.smembers('ip:state:%s' % state)
        except Exception, e:
            return 'Error: %s' % e
            
        res = list(result)
        res.reverse()
        return res
        
    def set_value_in_ip(self, ip, key, value):
        """ Set/add value in IP 
        keys: mac, opt82, state - can not be changed by this method
        """
        try:
            if key not in ['mac', 'opt82', 'state']:
                self._rh.hset('ip:%s' % ip, key, value)
                if key == 'session_id':
                    self._rh.hset('ip:lookup:sessid', value, ip)
            else:
                raise('%s can not be changed!' % key)
        except Exception, e:
            return 'Error: %s' % e
    
    def remove_key_from_lookup(self, option, key):
        """ Remove item from lookup table """
        try:
            if option == 'mac':
                self._rh.hdel('ip:lookup:mac', key)
            elif option == 'opt32':
                self._rh.hdel('ip:lookup:opt32', key)
            elif option == 'sessid':
                self._rh.hdel('ip:lookup:sessid', key)
        except Exception, e:
            return 'Error: %s' % e
    
    def remove_key_from_ip_table(self, ip, key):
        try:
            self._rh.hdel('ip:%s' % ip, key)
        except Exception, e:
            return 'Error: %s' % e

if __name__ == "__main__":
    red = RedisMethods()
    if len(sys.argv) == 2:
        if 'add' == sys.argv[1]:
            for i in range(0, 5):
                val = random.randint(0, 999999)
                red.create_ip({'ip': '%s'%val, 'mac': 'mac%s'%val, 'opt82': 'opt%s'%val, 'state': '0'})
        if 'getstate' == sys.argv[1]:
            print red.get_ip_by_state(0)
    #red.create_ip({'ip': '1', 'mac': 'mac1', 'opt82': 'opt1', 'state': '1'})
    #red.create_ip({'ip': '2', 'mac': 'mac2', 'opt82': 'opt2', 'state': '1'})
    #print 'ok'
    #red.remove_ip('2')
    #print 'ok'    
    #r = red.get_data('ip', '1')
    #r2 = red.get_data('mac', 'mac1')
    #r3 = red.get_data('opt82', 'opt1')
    #print str(r)+'\n'+str(r2)+'\n'+str(r3)
    #red.update_data('1', {'mac': 'mac_n', 'opt82': 'opt_n', 'state': '2'})
    #print 'ok'    
    #r = red.get_ip_by_state('2')
    #print r
