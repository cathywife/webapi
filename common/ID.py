# -*- coding: utf-8 -*-
import logging
import string
import web

class ID:

    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.logger = logging.getLogger('cmdbapi')

    def getCITypeID(self):
        try:
            result = self.db.query('select max(id) ID from t_citype')
        except Exception as e:
            self.logger.error(e)
            return None

        id = result[0]['ID']
        if id is None:
            id = 'PCIT00000001'
        else:
            id = 'PCIT' + str(string.atoi(id[4:]) + 1).rjust(8, '0')

        return id

    def getCITypeFid(self):
        try:
            result = self.db.query('select max(fid) FID from t_citype')
        except Exception as e:
            self.logger.error(e)
            return None

        fid = result[0]['FID']
        if fid is None:
            fid = 'FCIT00000001'
        else:
            fid = 'FCIT' + str(string.atoi(fid[4:]) + 1).rjust(8, '0')

        return fid

    def getAttrTypeID(self):
        try:
            result = self.db.query('select max(id) ID from T_ATTRTYPE')
        except Exception as e:
            self.logger.error('获取ATTRTYPE最大ID失败，',e)
            return None

        id = result[0]['ID']
        if id is None:
            id = 'PCAT00000001'
        else:
            id = 'PCAT' + str(string.atoi(id[4:]) + 1).rjust(8, '0')

        return id

    def getAttrTypeFid(self):
        try:
            result = self.db.query('select max(fid) FID from T_ATTRTYPE')
        except Exception as e:
            self.logger.error('获取ATTRTYPE最大FID失败，',e)
            return None

        fid = result[0]['FID']
        if fid is None:
            fid = 'FCAT00000001'
        else:
            fid = 'FCAT' + str(string.atoi(fid[4:]) + 1).rjust(8, '0')

        return fid

    def getRelaTypeID(self):
        try:
            result = self.db.query('select max(id) ID from T_RELATYPE')
        except Exception as e:
            self.logger.error('获取RELATYPE最大ID失败，',e)
            return None

        id = result[0]['ID']
        if id is None:
            id = 'PCRT00000001'
        else:
            id = 'PCRT' + str(string.atoi(id[4:]) + 1).rjust(8, '0')

        return id

    def getRelaTypeFid(self):
        try:
            result = self.db.query('select max(fid) FID from T_RELATYPE')
        except Exception as e:
            self.logger.error('获取RELATYPE最大FID失败，',e)
            return None

        fid = result[0]['FID']
        if fid is None:
            fid = 'FCRT00000001'
        else:
            fid = 'FCRT' + str(string.atoi(fid[4:]) + 1).rjust(8, '0')

        return fid

    def getCIID(self):
        try:
            result = self.db.query('select max(id) ID from T_CI')
        except Exception as e:
            self.logger.error('获取CI最大ID失败，',e)
            return None

        id = result[0]['ID']
        if id is None:
            id = 'PCID00000001'
        else:
            id = 'PCID' + str(string.atoi(id[4:]) + 1).rjust(8, '0')

        return id

    def getCIFid(self):
        try:
            result = self.db.query('select max(fid) FID from T_CI')
        except Exception as e:
            self.logger.error('获取CI最大FID失败，',e)
            return None

        fid = result[0]['FID']
        if fid is None:
            fid = 'FCID00000001'
        else:
            fid = 'FCID' + str(string.atoi(fid[4:]) + 1).rjust(8, '0')

        return fid

    def getAttrID(self):
        try:
            result = self.db.query('select max(id) ID from T_ATTR')
        except Exception as e:
            self.logger.error('获取ATTR最大ID失败，',e)
            return None

        id = result[0]['ID']
        if id is None:
            id = 'PCAD00000001'
        else:
            id = 'PCAD' + str(string.atoi(id[4:]) + 1).rjust(8, '0')

        return id

    def getAttrFid(self):
        try:
            result = self.db.query('select max(fid) FID from T_ATTR')
        except Exception as e:
            self.logger.error('获取ATTR最大FID失败，',e)
            return None

        fid = result[0]['FID']
        if fid is None:
            fid = 'FCAD00000001'
        else:
            fid = 'FCAD' + str(string.atoi(fid[4:]) + 1).rjust(8, '0')

        return fid

    def getRelaFid(self):
        try:
            result = self.db.query('select max(fid) FID from T_RELA')
        except Exception as e:
            self.logger.error('获取RELA最大FID失败，',e)
            return None

        fid = result[0]['FID']
        if fid is None:
            fid = 'FCRD00000001'
        else:
            fid = 'FCRD' + str(string.atoi(fid[4:]) + 1).rjust(8, '0')

        return fid