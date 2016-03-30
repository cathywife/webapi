# -*- coding: utf-8 -*-

import json
import logging
import sys

import web

from common.ID import ID
from common.Time import Time

reload(sys)
sys.setdefaultencoding('utf-8')

class attr:
    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.id = ID()
        self.time = Time()
        self.logger = logging.getLogger('cmdbapi')

    def createAttr(self, id, fid, type_fid, ci_fid, value, description, owner,
                 log, starttime, endtime):
        if id is None or fid is None or type_fid is None or ci_fid is None or \
           value is None or starttime is None or endtime is None:
            self.logger.error('[ATTR.CREATEATTR] 创建ATTR[ID:%S, FID:%S]失败: 参数[ID|FID|TYPE_FID|CI_FID|VALUE'
                              '|STARTTIME|ENDTIME]不可为空.' % id, fid)
            return None

        try:
            result = self.db.insert('T_ATTR', id=id, fid=fid, type_fid=type_fid, ci_fid=ci_fid,
                                    value=value, description=description, owner=owner,
                                    log=log, starttime=starttime, endtime=endtime)
        except Exception as e:
            self.logger.error('[ATTR.CREATEATTR] 创建ATTR[ID:%S, FID:%S]失败: %s.' % id, fid, e)
        else:
            return fid

    def GET(self):
        result = web.input()
        params = {
            'id': result.get('id'),
            'fid': result.get('fid'),
            'type_fid': result.get('type_fid'),
            'ci_fid':result.get('ci_fid'),
            'value': result.get('value'),
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
            queryResult = self.db.query('SELECT * FROM T_ATTR where ' + conditions)
            attrList = []
            for each in queryResult:
                attrList.append(each)
        except Exception as e:
            self.logger.error('[ATTR.GET] 查询ATTR失败: %s' % e)
            return 1
        else:
            self.logger.info('[ATTR.GET] 查询ATTR, 条件为: %s' % conditions)

        return json.dumps(attrList, indent=2, ensure_ascii=False, separators=(',', ':')).decode('utf-8')

    def POST(self):
        result = web.input()
        params = {
            'type_fid':result.get('type_fid'),
            'ci_fid':result.get('ci_fid'),
            'value':result.get('value'),
            'description':result.get('description'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }

        id = self.id.getAttrID()
        fid = self.id.getAttrFid()
        if id is None or fid is None:
            self.logger.error("[ATTR.POST] 获取ID和FID失败")
            return 1

        try:
            starttime = self.time.getNow()
            endtime = self.time.getEndTime()
            attrtype = self.db.query('SELECT distinct a.fid , b.fid FROM T_CI a, T_ATTRTYPE b '
                                     'WHERE a.fid=$cifid and a.endtime=$endtime and b.fid=$ciattrtypefid '
                                     'and b.endtime=$endtime and a.type_fid=b.citype_fid',
                                     vars={'endtime':endtime,'cifid':params['ci_fid'],
                                           'ciattrtypefid':params['type_fid']})
            attrtype = list(attrtype)
            if len(attrtype) <> 1:
                self.logger.error('[ATTR.POST] 验证TYPE_FID唯一性失败')
                return 1
            attr = self.createAttr(id=id, fid=fid, type_fid=params['type_fid'], ci_fid=params['ci_fid'],
                             value=params['value'], description=params['description'], owner=params['owner'],
                             log=params['log'], starttime=starttime, endtime=endtime)
            if attr is None:
                return 2
            else:
                self.logger.info("[ATTR.POST] 创建ATTR[ID:%s，FID:%s]" % id, fid)
                return fid

        except Exception as e:
            self.logger.error('[ATTR.POST] 查询TYPE_FID唯一性失败. %s' % e)
            return 1

    def PUT(self):
        result = web.input()
        params = {
            'fid':result.get('fid'),
            'value':result.get('value'),
            'description':result.get('description'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }
        fid = params['fid']
        if fid is None:
            self.logger.error("[ATTR.PUT] 更新ATTR失败: 输入参数FID为空")
            return 1
        elif params.values().count(not None) == 1:
            self.logger.error("[ATTR.PUT] 更新ATTR失败: 无待更新字段")
            return 1

        try:
            endtime = self.time.getEndTime()
            try:
                attr = self.db.query("SELECT * FROM T_ATTR WHERE endtime = $endtime and fid = $fid",
                                       vars={'endtime':endtime,'fid':fid})
                attr = list(attr)
            except Exception as e:
                self.logger.error('[ATTR.PUT] 更新ATTR失败: 查找FID=%s的ATTR项失败. %s' % fid, e)
                return 2
            else:
                if len(attr) <> 1:
                    self.logger.error('[ATTR.PUT] 更新ATTR失败: 查找FID=%s, endtime=%s的ATTR不唯一' %
                                      fid, endtime)
                    return 2

            params = {
                'type_fid':attr[0]['TYPE_FID'],
                'ci_fid':attr[0]['CI_FID'],
                'value':result.get('value', attr[0]['VALUE']),
                'description':result.get('description', attr[0]['DESCRIPTION']),
                'owner':result.get('owner', attr[0]['OWNER']),
                'log':result.get('log', attr[0]['LOG']),
            }

            updatetime = self.time.getNow()
            n = self.db.update('T_ATTR', where='fid = $fid and endtime = $endtime',
                      vars={'fid':fid, 'endtime': endtime}, endtime=updatetime)
            if n <> 1:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 更新记录ENDTIME字段失败")
                return 2

            id = self.id.getAttrID()
            if id is None:
                self.logger.error("[ATTR.PUT] 更新ATTR失败: 生成ID失败")
                return 2
            updateAttr = self.createAttr(id=id, fid=fid, type_fid=params['type_fid'], ci_fid=params['ci_fid'],
                             value=params['value'], description=params['description'], owner=params['owner'],
                             log=params['log'], starttime=updatetime, endtime=endtime)
        except Exception as e:
            self.logger.error('[ATTR.PUT] 更新ATTR失败: %s' % e)
            return 3
        else:
            if updateAttr is None:
                return 3
            else:
                self.logger.info('[ATTR.PUT] 更新ATTR, FID=%s' % fid)
                return fid




