# -*- coding: utf-8 -*-

import json
import logging
import sys

import web

from common.ID import ID
from common.Time import Time

reload(sys)
sys.setdefaultencoding('utf-8')

class ci:
    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.id = ID()
        self.time = Time()
        self.logger = logging.getLogger('cmdbapi')

    def createCI(self, id, fid, type_fid, name, description, tag, priority, owner,
                 log, starttime, endtime):
        if id is None or fid is None or type_fid is None or name is None or \
           priority is None or starttime is None or endtime is None:
            self.logger.error('[CI.CREATECI] 创建CI[ID:%S, FID:%S]失败: 参数[ID|FID|TYPE_FID|NAME|PRIORITY'
                              '|STARTTIME|ENDTIME]不可为空.' % id, fid)
            return None

        try:
            result = self.db.insert('T_CI', id=id, fid=fid, type_fid=type_fid, name=name,
                                    description=description, tag=tag, priority=priority, owner=owner,
                                    log=log, starttime=starttime, endtime=endtime)
        except Exception as e:
            self.logger.error('[CI.CREATECI] 创建CI[ID:%S, FID:%S]失败: %s.' % id, fid, e)
        else:
            return fid

    def GET(self):
        result = web.input()
        params = {
            'id': result.get('id'),
            'fid': result.get('fid'),
            'type_fid': result.get('type_fid'),
            'name': result.get('name'),
            'tag': result.get('tag'),
            'priority':result.get('priority'),
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
            queryResult = self.db.query('SELECT * FROM T_CI where ' + conditions)
            ciList = []
            for each in queryResult:
                ciList.append(each)
        except Exception as e:
            self.logger.error('[CI.GET] 查询CI失败: %s' % e)
            return 1
        else:
            self.logger.info('[CI.GET] 查询CI, 条件为: %s' % conditions)

        return json.dumps(ciList, indent=2, ensure_ascii=False, separators=(',', ':')).decode('utf-8')

    def POST(self):
        result = web.input()
        params = {
            'type_fid':result.get('type_fid'),
            'name':result.get('name'),
            'description':result.get('description'),
            'tag':result.get('tag'),
            'priority':result.get('priority'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }

        id = self.id.getCIID()
        fid = self.id.getCIFid()
        if id is None or fid is None:
            self.logger.error("[CI.POST] 获取ID和FID失败")
            return 1

        try:
            starttime = self.time.getNow()
            endtime = self.time.getEndTime()
            citype = self.db.query('SELECT distinct fid FROM T_CITYPE WHERE endtime = $endtime and '
                                 'fid = $type_fid',vars={'endtime':endtime,'type_fid':params['type_fid']})
            citype = list(citype)
            if len(citype) <> 1:
                self.logger.error('[CI.POST] 验证TYPE_FID唯一性失败')
                return 1

            ci = self.createCI(id=id, fid=fid, type_fid=params['type_fid'], name=params['name'],
                               description=params['description'], tag=params['tag'], priority=params['priority'],
                               owner=params['owner'], log=params['log'], starttime=starttime, endtime=endtime)
            if ci is None:
                return 2
            else:
                self.logger.info("[CI.POST] 创建CI[ID:%s，FID:%s]" % id, fid)
                return fid

        except Exception as e:
            self.logger.error('[CI.POST] 查询TYPE_FID唯一性失败. %s' % e)
            return 1

    def PUT(self):
        result = web.input()
        params = {
            'fid':result.get('fid'),
            'name':result.get('name'),
            'description':result.get('description'),
            'tag':result.get('tag'),
            'priority':result.get('priority'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }
        fid = params['fid']
        if fid is None:
            self.logger.error("[CI.PUT] 更新CI失败: 输入参数FID为空")
            return 1
        elif params.values().count(not None) == 1:
            self.logger.error("[CI.PUT] 更新CI失败: 无待更新字段")
            return 1

        try:
            endtime = self.time.getEndTime()
            try:
                ci = self.db.query("SELECT * FROM T_CI WHERE endtime = $endtime and fid = $fid",
                                       vars={'endtime':endtime,'fid':fid})
                ci=list(ci)
            except Exception as e:
                self.logger.error('[CI.PUT] 更新CI失败: 查找FID=%s的CI项失败. %s' % fid, e)
                return 2
            else:
                if len(ci) <> 1:
                    self.logger.error('[CI.PUT] 更新CI失败: 查找FID=%s, endtime=%s的CI不唯一' %
                                      fid, endtime)
                    return 2

            params = {
                'type_fid':ci[0]['TYPE_FID'],
                'name':result.get('name', ci[0]['NAME']),
                'description':result.get('description', ci[0]['DESCRIPTION']),
                'tag':result.get('tag', ci[0]['TAG']),
                'priority':result.get('priority', ci[0]['PRIORITY']),
                'owner':result.get('owner', ci[0]['OWNER']),
                'log':result.get('log', ci[0]['LOG']),
            }

            updatetime = self.time.getNow()
            n = self.db.update('T_CI', where='fid = $fid and endtime = $endtime',
                      vars={'fid':fid, 'endtime': endtime}, endtime=updatetime)
            if n <> 1:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 更新记录ENDTIME字段失败")
                return 2

            id = self.id.getCIID()
            if id is None:
                self.logger.error("[CI.PUT] 更新CI失败: 生成ID失败")
                return 2
            updateCI = self.createCI(id=id, fid=fid, type_fid=params['type_fid'], name=params['name'],
                               description=params['description'], tag=params['tag'], priority=params['priority'],
                               owner=params['owner'], log=params['log'], starttime=updatetime, endtime=endtime)
        except Exception as e:
            self.logger.error('[CI.PUT] 更新CI失败: %s' % e)
            return 3
        else:
            if updateCI is None:
                return 3
            else:
                self.logger.info('[CI.PUT] 更新CI, FID=%s' % fid)
                return fid