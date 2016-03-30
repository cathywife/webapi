# -*- coding: utf-8 -*-

import web

class database:
    dblist = ('oracle', 'mysql')

    def __init__(self):
        self.dbsocket = ''
        self.__db__ = ''
        self.__user__ = ''
        self.__passwd__ = ''

    def connetions(self, dbname, database, user, passwd):
        if dbname not in self.dblist:
            print 'you are wrong'
            return None
    
        try:
            self.dbsocket = web.database(dbn= dbname, user=user, pw=passwd, db=database)
        except  Exception:
            return Exception

        return self.dbsocket


