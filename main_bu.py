import redis
import sys
sys.path.append("/opt/redis_methods/")

'''
for me:
1) use Pipelines!
2) fix return in get_ip_by_state()
'''

class redis_methods():
    '''
    self._field_name_lookup_mac = 'lookup:mac'
    self._field_name_lookup_opt82 = 'lookup:opt82'
    self._field_name_ip = 'ip'
    self._field_name_ip = 'state'
    '''

    def __init__(self):
        self._rh = redis.StrictRedis(host='localhost', port=6379, db=0)

    def create_ip(self, ip_data):
        ''' Create an item in Redis '''
        ip = ip_data['ip']
        del ip_data['ip']
        if 'state' in ip_data:
            ip_data['state'] = '0'
        try:
            self._rh.hmset('ip:%s' % ip, ip_data)

            self._rh.hset('ip:lookup:mac', ip_data['mac'], ip)
            self._rh.hset('ip:lookup:opt82', ip_data['opt82'], ip)

            self._rh.sadd('ip:state:0', ip)
        except Exception, e:
            return 'Error: %s' % e

    def remove_ip(self, ip):
        ''' Delete item from Redis '''
        try:
            mac = self._rh.hget('ip:%s' % ip, 'mac')
            opt82 = self._rh.hget('ip:%s' % ip, 'opt82')
            state = self._rh.hget('ip:%s' % ip, 'state')
        except Exception, e:
            return 'Error: %s' % e
        
        try:
            self._rh.delete('ip:%s' % ip)
            self._rh.hdel('ip:lookup:mac', mac)
            self._rh.hdel('ip:lookup:opt82', opt82)
            self._rh.srem('ip:state:%s' % state, ip)
        except Exception, e:
            return 'Error: %s' % e
        
    def get_data(self, item, value):
        ''' '''
        try:
            if item == 'ip':
                result = self._rh.hgetall('ip:%s' % value)
            elif item == 'mac':
                item_ip = self._rh.hget('ip:lookup:mac', value)
                result = self._rh.hgetall('ip:%s' % item_ip)
            elif item == 'opt82':
                item_ip = self._rh.hget('ip:lookup:opt82', value)
                result = self._rh.hgetall('ip:%s' % item_ip)
        except Exception, e:
            return 'Error: %s' % e
        
        return result
        
    def update_data(self, ip, new_data):
        ''' '''
        try:
            #ip = new_data['ip']
            mac = self._rh.hget('ip:%s' % ip, 'mac')
            opt82 = self._rh.hget('ip:%s' % ip, 'opt82')
            state = self._rh.hget('ip:%s' % ip, 'state')
            #del new_data['ip']
        except Exception, e:
            return 'Error: %s' % e
        try:
            self._rh.hmset('ip:%s' % ip, new_data)
            
            self._rh.hdel('ip:lookup:mac', mac)
            self._rh.hdel('ip:lookup:opt82', mac)
            self._rh.hset('ip:lookup:mac', new_data['mac'], ip)
            self._rh.hset('ip:lookup:opt82', new_data['opt82'], ip)

            self._rh.srem('ip:state:%s' % state, ip)
            self._rh.sadd('ip:state:%s' % new_data['state'], ip)
        except Exception, e:
            return 'Error: %s' % e
            
    def get_ip_by_state(self, state):
        ''' '''
        try:
            result = self._rh.smembers('ip:state:%s' % state)
        except Exception, e:
            return 'Error: %s' % e
            
        return result

if __name__ == "__main__":
    red = redis_methods()
    
    #red.create_ip({'ip': '127.0.0.1', 'mac': '2222', 'opt82': '9090', 'state': '1'})
    #red.create_ip({'ip': '111.11.1.0', 'mac': 'ddsw', 'opt82': '8080', 'state': '1'})
    #print 'ok'
    #red.remove_ip('127.0.0.1')
    #print 'ok'    
    #r = red.get_data('ip', '127.0.0.1')
    #r2 = red.get_data('mac', '2222')
    #r3 = red.get_data('opt82', '9090')
    #print str(r)+'\n'+str(r2)+'\n'+str(r3)
    #red.update_data('127.0.0.1', {'mac': 'lion3', 'opt82': '111', 'state': '2'})
    #print 'ok'    
    #r = red.get_ip_by_state('2')
    #print r
