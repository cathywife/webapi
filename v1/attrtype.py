# -*- coding: utf-8 -*-

import json
import logging
import sys

import web

from common.ID import ID
from common.Time import Time

reload(sys)
sys.setdefaultencoding('utf-8')

class attrtype:
    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.id = ID()
        self.time = Time()
        self.logger = logging.getLogger('cmdbapi')

    def createAttrType(self, id, fid, name, displayname, description, citype_fid, mandatory, owner,
                       log, starttime, endtime):
        if id is None or fid is None or name is None or displayname is None or \
           citype_fid is None or mandatory is None or starttime is None or endtime is None:
            self.logger.error('[ATTRTYPE.CREATEATTRTYPE] 创建ATTRTYPE[ID:%S, FID:%S]失败: 参数[ID|FID|NAME|'
                              'DISPLAYNAME|CITYPE_FID|MANDATORY|STARTTIME|ENDTIME]不可为空.' % (id, fid))
            return None

        try:
            result = self.db.insert('T_ATTRTYPE', id=id, fid=fid, name=name, displayname=displayname,
                                    description=description, citype_fid=citype_fid, mandatory=mandatory,
                                    owner=owner, log=log, starttime=starttime, endtime=endtime)
        except Exception as e:
            self.logger.error('[ATTRTYPE.CREATEATTRTYPE] 创建ATTRTYPE[ID:%s, FID:%s]失败: %s.' % (id, fid, e))
        else:
            return fid

    def deleteAttrType(self, fid, currentTime, log):
        if fid is None or currentTime is None:
            self.logger.error('FID或者当前时间字段为空，无法删除ATTRTYPE记录')
            return False

        try:
            attrtype = self.db.query("T_CITYPE", where='endtime = $endtime and fid = $fid',
                              vars={'endtime':self.time.getEndTime(), 'fid':fid})
            # 将attrtype的endtime字段更新为当前时间
            self.db.update('T_ATTRTYPE', where='fid=$fid and endtime=$endtime',
                      vars={'fid':fid,'endtime':self.time.getEndTime()}, endtime=currentTime)
            if len(attrtype) <> 1:
                self.logger.error('查询出的ATTRTYPE记录不唯一')
                return False
        except Exception as e:
            self.logger.error('查询或者更新ATTRTYPE失败，%s', e)
            return False

        deleteResult = self.createCIType(attrtype[0]['ID'], attrtype[0]['FID'], attrtype[0]['NAME'],
                          attrtype[0]['DESCRIPTION'], attrtype[0]['CITYPE_FID'],attrtype[0]['MANDATORY'],
                          attrtype[0]['OWNER'], attrtype[0]['STARTTIME'], self.time.getDelTime(),log)
        if deleteResult == fid:
            return True
        else:
            self.logger.error('删除ATTRTYPE[FID:%S]出错', fid)
            return False

    def GET(self):
        result = web.input()
        params = {
            'id': result.get('id'),
            'fid': result.get('fid'),
            'name': result.get('name'),
            'displayname': result.get('displayname'),
            'citype_fid': result.get('citype_fid'),
            'mandatory': result.get('mandatory'),
            'owner': result.get('owner'),
            'time':result.get('time'),
        }

        listparams = [ k+'= \''+v + '\'' for k, v in params.iteritems() if not v is None ]
        conditions = " and ".join(listparams)
        endtime = self.time.getEndTime()

        timearea = ''
        # 定义查询时间条件语句
        if params['time']:
            timearea = 'starttime <= ' + params['time'] + ' and endtime > ' + params['time']
        else:
            timearea = 'endtime = ' + endtime

        if conditions != '':
            conditions += ' and '
        conditions += timearea

        try:
            queryResult = self.db.query('SELECT * FROM T_ATTRTYPE where ' + conditions)
            attrtypeList = []
            for each in queryResult:
                attrtypeList.append(each)
        except Exception as e:
            self.logger.error('[ATTRTYPE.GET] 查询ATTRTYPE失败: %s' % e)
            return 1
        else:
            self.logger.info('[ATTRTYPE.GET] 查询ATTRTYPE，条件为: %s' % conditions)

        return json.dumps(attrtypeList, indent=2, ensure_ascii=False, separators=(',', ':')).decode('utf-8')

    def POST(self):
        result = web.input()
        params = {
            'name': result.get('name'),
            'displayname': result.get('displayname'),
            'description': result.get('description'),
            'citype_fid': result.get('citype_fid'),
            'mandatory': result.get('mandatory'),
            'owner': result.get('owner'),
            'log': result.get('log'),
        }

        id = self.id.getAttrTypeID()
        fid = self.id.getAttrTypeFid()
        if id is None or fid is None:
            self.logger.error("[ATTRTYPE.POST] 获取ID和FID失败")
            return 1

        startTime = self.time.getNow()
        endTime = self.time.getEndTime()
        attrtype = self.createAttrType(id=id, fid=fid, name=params['name'], displayname=params['displayname'],
                                       description=params['description'], citype_fid=params['citype_fid'],
                                       mandatory=params['mandatory'], owner=params['owner'], log=params['log'],
                                       starttime=startTime, endtime=endTime )
        if attrtype is None:
            return 2
        else:
            self.logger.info("[ATTRTYPE.POST] 创建ATTRTYPE[ID:%s，FID:%s]" % (id, fid))
            return fid

    def PUT(self):
        result = web.input()
        params = {
            'fid' : result.get('fid'),
            'name': result.get('name'),
            'displayname' : result.get('displayname'),
            'description': result.get('description'),
            'mandatory' : result.get('mandatory'),
            'owner': result.get('owner'),
            'log': result.get('log'),
        }

        fid = params['fid']
        if fid is None :
            self.logger.error("[ATTRTYPE.PUT] 更新ATTRTYPE失败: 输入参数FID为空")
            return 1
        elif params.values().count(not None) == 1:
            self.logger.error("[ATTRTYPE.PUT] 更新ATTRTYPE失败: 无待更新字段")
            return 1

        try:
            endtime = self.time.getEndTime()
            try:
                attrtype = self.db.query("SELECT * FROM T_ATTRTYPE WHERE endtime = $endtime and fid = $fid ",
                                         vars={'endtime':endtime, 'fid':fid})
                attrtype = list(attrtype)
            except Exception as e:
                self.logger.error('[ATTRTYPE.PUT] 更新ATTRTYPE失败: 查找FID=%s的ATTRTYPE项失败. %s' % (fid, e))
                return 2
            else:
                if len(attrtype) <> 1:
                    self.logger.error('[ATTRTYPE.PUT] 更新CITYPE失败: 查找FID=%s, endtime=%s的ATTRTYPE不唯一' %
                                      (fid, endtime))
                    return 2

            params = {
                'name': result.get('name', attrtype[0]['NAME']),
                'displayname' : result.get('displayname', attrtype[0]['DISPLAYNAME']),
                'description': result.get('description', attrtype[0]['DESCRIPTION']),
                'mandatory' : result.get('mandatory', attrtype[0]['MANDATORY']),
                'citype_fid': attrtype[0]['CITYPE_FID'],
                'owner': result.get('owner', attrtype[0]['OWNER']),
                'log': result.get('log', attrtype[0]['LOG']),
            }

            startTime = self.time.getNow()
            n = self.db.update('T_ATTRTYPE', where='fid = $fid and endtime = $endtime',
                               vars={'fid':fid, 'endtime': endtime}, endtime=startTime)

            if n <> 1:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 更新记录ENDTIME字段失败")
                return 2

            id = self.id.getAttrTypeID()
            if id is None:
                self.logger.error("[ATTRTYPE.PUT] 更新ATTRTYPE失败: 生成ID失败")
                return 2
            updateAttrType = self.createAttrType(id=id, fid=fid, name=params['name'], displayname=params['displayname'],
                                                 description=params['description'], citype_fid=params['citype_fid'],
                                                 mandatory=params['mandatory'], owner=params['owner'], log=params['log'],
                                                 starttime=startTime, endtime=endtime )
        except Exception as e:
            self.logger.error('[ATTRTYPE.PUT] 更新ATTRTYPE失败: %s' % e)
            return 3
        else:
            if updateAttrType is None:
                return 3
            else:
                self.logger.info('[ATTRTYPE.PUT] 更新ATTRTYPE, FID=%s' % fid)
                return fid