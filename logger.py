#!/usr/bin/python
"""
format=%(asctime)s.%(msecs)-3d %(levelname)s in '%(module)s' at line %(lineno)d: %(message)s
"""
import sys
import os
import logging
import logging.config

class BrasLogger(object):
    def __init__(self, option={}):
        """ """
        self._debug = logging.DEBUG
        self._info = logging.INFO
        self._warn = logging.WARN
        self._error = logging.ERROR
        self._critical = logging.CRITICAL
        
        self._logger = logging.getLogger('main')
        self._logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        self._logger.addHandler(handler)
        
        handler = logging.FileHandler('my.log', 'a')
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
    
    def setup_config_file(self, config_log_file='bras_log.conf'):
        """ """
        logging.config.fileConfig(config_log_file)
        self._logger = logging.getLogger('main')
        
    def add_log(self, level, info_msg=''):
        """ """
        self._logger.log(level, info_msg)
    
    
