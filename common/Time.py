# -*- coding: utf-8 -*-

import time

class Time:
    def __init__(self):
        self.__ENDTIME__ = str(int('99991231235959'))
        self.__DELETETIME__ = str('00000000000000')

    def getNow(self):
        return time.strftime("%Y%m%d%H%M%S", time.localtime())

    def getEndTime(self):
        return self.__ENDTIME__

    def getDelTime(self):
        return self.__DELETETIME__
