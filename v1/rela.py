# -*- coding: utf-8 -*-

import json
import logging
import sys

import web

from common.ID import ID
from common.Time import Time

reload(sys)
sys.setdefaultencoding('utf-8')

class rela:
    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.id = ID()
        self.time = Time()
        self.logger = logging.getLogger('cmdbapi')

    def createRela(self, sfid, dfid, fid, type_fid, owner, log, starttime, endtime):
        if sfid is None or dfid is None or fid is None or type_fid is None or  \
           starttime is None or endtime is None:
            self.logger.error('[RELA.CREATERELA] 创建RELA[ID:%S, FID:%S]失败: 参数[SFID|DFID|FID|TYPE_FID|'
                              '|STARTTIME|ENDTIME]不可为空.' % id, fid)
            return None

        try:
            result = self.db.insert('T_RELA', sfid=sfid, dfid=dfid, fid=fid, type_fid=type_fid,
                                    owner=owner, log=log, starttime=starttime, endtime=endtime)
        except Exception as e:
            self.logger.error('[RELA.CREATERELA] 创建RELA[ID:%S, FID:%S]失败: %s.' % id, fid, e)
        else:
            return fid

    def GET(self):
        result = web.input()
        params = {
            'sfid': result.get('id'),
            'dfid': result.get('fid'),
            'fid': result.get('type_fid'),
            'type_fid':result.get('ci_fid'),
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
            relaList = []
            for each in queryResult:
                relaList.append(each)
        except Exception as e:
            self.logger.error('[RELA.GET] 查询RELA失败: %s' % e)
            return 1
        else:
            self.logger.info('[RELA.GET] 查询RELA, 条件为: %s' % conditions)

        return json.dumps(relaList, indent=2, ensure_ascii=False, separators=(',', ':')).decode('utf-8')

    def POST(self):
        result = web.input()
        params = {
            'sfid':result.get('sfid'),
            'dfid':result.get('dfid'),
            'relation':result.get('relation'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }

        id = self.id.getAttrID()
        fid = self.id.getAttrFid()
        if id is None or fid is None:
            self.logger.error("[RELA.POST] 获取ID和FID失败")
            return 1

        try:

            starttime = self.time.getNow()
            endtime = self.time.getEndTime()
            relatype = self.db.query('SELECT distinct a.fid type_fid, b.fid sfid, c.fid dfid FROM T_RELATYPE a, T_CI b, T_CI c '
                                   'WHERE a.relation = $relation and b.fid = $sfid and c.fid = $dfid and '
                                   'a.stype_fid = b.type_fid and a.dtype_fid = c.type_fid and '
                                   'a.endtime=$endtime and b.endtime=$endtime and c.endtime=$endtime',
                                   vars={'endtime':endtime,'relation':params['relation'],
                                         'sfid':params['sfid'],'dfid':params['dfid']})
            relatype = list(relatype)
            if len(relatype) <> 1:
                self.logger.error('[RELA.POST] 验证TYPE_FID唯一性失败')
                return 1

            rela = self.createRela(sfid=params['sfid'], dfid=params['dfid'], fid=fid, type_fid=relatype[0]['TYPE_FID'],
                                   owner=params['owner'], log=params['log'], starttime=starttime, endtime=endtime)
            if rela is None:
                return 2
            else:
                self.logger.info("[RELA.POST] 创建RELA[ID:%s，FID:%s]" % id, fid)
                return fid

        except Exception as e:
            self.logger.error('[RELA.POST] 查询TYPE_FID唯一性失败. %s' % e)
            return 1

    def PUT(self):
        result = web.input()
        params = {
            'fid':result.get('fid'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }
        fid = params['fid']
        if fid is None:
            self.logger.error("[RELA.PUT] 更新RELA失败: 输入参数FID为空")
            return 1
        elif params.values().count(not None) == 1:
            self.logger.error("[RELA.PUT] 更新RELA失败: 无待更新字段")
            return 1

        try:
            endtime = self.time.getEndTime()
            try:
                rela = self.db.query("SELECT * FROM T_RELA WHERE endtime = $endtime and fid = $fid",
                                       vars={'endtime':endtime,'fid':fid})
                rela=list(rela)
            except Exception as e:
                self.logger.error('[RELA.PUT] 更新RELA失败: 查找FID=%s的CITYPE项失败. %s' % fid, e)
                return 2
            else:
                if len(rela) <> 1:
                    self.logger.error('[RELA.PUT] 更新RELA失败: 查找FID=%s, endtime=%s的RELA不唯一' %
                                      fid, endtime)
                    return 2

            params = {
                'sfid':rela[0]['SFID'],
                'dfid':rela[0]['DFID'],
                'type_fid':rela[0]['TYPE_FID'],
                'owner':result.get('owner', rela[0]['OWNER']),
                'log':result.get('log', rela[0]['LOG']),
            }

            updatetime = self.time.getNow()
            n = self.db.update('T_RELA', where='fid = $fid and endtime = $endtime',
                      vars={'fid':fid, 'endtime': endtime}, endtime=updatetime)
            if n <> 1:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 更新记录ENDTIME字段失败")
                return 2

            if id is None:
                self.logger.error("[RELA.PUT] 更新RELA失败: 生成ID失败")
                return 2
            updateCI = self.self.createRela(sfid=params['sfid'], dfid=params['dfid'], fid=fid, type_fid=params['type_fid'],
                                   owner=params['owner'], log=params['log'], starttime=updatetime, endtime=endtime)
        except Exception as e:
            self.logger.error('[RELA.PUT] 更新RELA失败: %s' % e)
            return 3
        else:
            if updateCI is None:
                return 3
            else:
                self.logger.info('[RELA.PUT] 更新RELA, FID=%s' % fid)
                return fid