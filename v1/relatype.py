# -*- coding: utf-8 -*-

import json
import logging
import sys
import demjson

import web

from common.ID import ID
from common.Time import Time

reload(sys)
sys.setdefaultencoding('utf-8')

class relatype:
    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.id = ID()
        self.time = Time()
        self.logger = logging.getLogger('cmdbapi')

    def createRelaType(self, id, stype_fid, dtype_fid, fid, name, relation, owner,
                       log, starttime,endtime):
        if id is None or stype_fid is None or dtype_fid is None or \
           fid is None or name is None or relation is None or starttime is None or endtime is None:
            self.logger.error('[RELATYPE.CREATERELATYPE] 创建RELATYPE[ID:%S, FID:%S]失败: 参数[ID|STYPE_FID|'
                              'DTYPE_FID|FID|NAME|RELATION|STARTTIME|ENDTIME]不可为空.' % (id, fid))
            return None

        try:
            result = self.db.insert('T_RELATYPE', id=id, stype_fid=stype_fid, dtype_fid=dtype_fid,
                                    fid=fid, name=name, relation=relation, owner=owner, log=log,
                                    starttime=starttime, endtime=endtime)
        except Exception as e:
            self.logger.error('[RELATYPE.CREATERELATYPE] 创建RELATYPE[ID:%S, FID:%S]失败: %s.' % (id, fid, e))
        else:
            return fid

    def GET(self):
        '''
        GET方法，实现API查询
        :return: 1：执行查询语句时失败
                 json格式文本：查询成功，返回查找出的数据
        '''
        result = web.input()
        params = {
            'id': result.get('id'),
            'stype_fid': result.get('stype_fid'),
            'dtype_fid': result.get('dtype_fid'),
            'fid': result.get('fid'),
            'name': result.get('name'),
            'relation': result.get('relation'),
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
            queryResult = self.db.query('SELECT * FROM T_RELATYPE where ' + conditions)
            relatypeList = []
            for each in queryResult:
                relatypeList.append(each)
        except Exception as e:
            self.logger.error('[RELATYPE.GET] 查询RELATYPE失败: %s' % e)
            return 1
        else:
            self.logger.info('[RELATYPE.GET] 查询RELATYPE，条件为: %s' % conditions)

        return json.dumps(relatypeList, indent=2, ensure_ascii=False, separators=(',', ':')).decode('utf-8')

    def POST(self):
        '''
        POST方法，实现API插入操作
        :return: 1：生成主键ID或者组ID失败
                 2：调用createCITYPE函数创建CI，返回值为None，表示插入失败
                 fid：插入成功，返回组ID
        '''
        result = web.input()
        params = {
            'stype_fid': result.get('stype_fid'),
            'dtype_fid': result.get('dtype_fid'),
            'name': result.get('name'),
            'relation': result.get('relation'),
            'owner': result.get('owner'),
            'log': result.get('log'),
        }

        id = self.id.getRelaTypeID()
        fid = self.id.getRelaTypeFid()

        try:
            starttime = self.time.getNow()
            endtime = self.time.getEndTime()
            citype = self.db.query('SELECT distinct a.fid, b.fid FROM T_CITYPE a, T_CITYPE b '
                                  'WHERE a.endtime = $endtime and a.fid = $sfid and '
                                  'b.endtime = a.endtime and b.fid = $dfid',
                                  vars={'endtime':endtime, 'sfid':params['stype_fid'],
                                        'dfid':params['dtype_fid']})

            citype = list(citype)
            if len(citype) <> 1:
                self.logger.error('[RELATYPE.POST] 验证STYPE_FID和DTYPE_FID唯一性失败')
                return 1

            relatypeFid = self.createRelaType(id=id, stype_fid=params['stype_fid'], dtype_fid=params['dtype_fid'],
                                              fid=fid, name=params['name'], relation=params['relation'],
                                              owner=params['owner'], log=params['log'], starttime=starttime, endtime=endtime)
            if relatypeFid is None:
                return 2
            else:
                self.logger.info("[RELATYPE.POST] 创建RELATYPE[ID:%S, FID:%S]" % (id, fid))
                return fid
        except Exception as e:
            self.logger.error('[RELATYPE.POST] 查询STYPE_FID和DTYPE_FID失败. %s' % e)
            return 1

    def PUT(self):
        '''
        PUT方法，实现API更新操作
        :return: 1：输入的参数fid为空
                 2：查询指定fid和endtime的citype时出错
                 3. 查询获得的citype记录为0
                 4. 查询获得的citype记录不为1
                 5. 更新citype的endtime字段失败
                 6. 插入citype记录失败
                 fid：更新操作执行成功
        '''
        result = web.input()
        params = {
            'fid' : result.get('fid'),
            'name': result.get('name'),
            'relation': result.get('relation'),
            'owner': result.get('owner'),
            'log': result.get('log'),
        }

        fid = params.get('fid')
        if fid is None:
            self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 输入参数FID为空")
            return 1
        elif params.values().count(not None) == 1:
            self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 无待更新字段")
            return 1

        try:
            endtime = self.time.getEndTime()
            try:
                relatype = self.db.query("SELECT * FROM T_RELATYPE WHERE endtime = $endtime and fid = $fid ",
                              vars={'endtime':endtime, 'fid':fid})
                relatype = list(relatype)
                print relatype
            except Exception as e:
                self.logger.error('[RELATYPE.PUT] 更新RELATYPE失败: 查找FID=%s的RELATYPE项失败. %s' % (fid, e))
                return 2
            else:
                if len(relatype) <> 1:
                    self.logger.error('[RELATYPE.PUT] 更新RELATYPE失败: 查找FID=%s, endtime=%s的RELATYPE不唯一' %
                                      (fid, endtime))
                    return 2

            params = {
                'stype_fid': relatype[0]['STYPE_FID'],
                'dtype_fid': relatype[0]['DTYPE_FID'],
                'name': result.get('name', relatype[0]['NAME']),
                'relation': result.get('relation', relatype[0]['RELATION']),
                'owner': result.get('owner', relatype[0]['OWNER']),
                'log': result.get('log', relatype[0]['LOG']),
            }

            starttime = self.time.getNow()
            id = self.id.getRelaTypeID()
            if id is None:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 生成ID失败")
                return 2

            n = self.db.update('T_RELATYPE', where='fid = $fid and endtime = $endtime',
                      vars={'fid':fid, 'endtime': endtime}, endtime=starttime)
            if n <> 1:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 更新记录ENDTIME字段失败")
                return 2

            updateAttrType = self.createRelaType(id=id, stype_fid=params['stype_fid'], dtype_fid=params['dtype_fid'],
                                                 fid=fid, name=params['name'], relation=params['relation'],
                                                 owner=params['owner'], log=params['log'], starttime=starttime, endtime=endtime)

        except Exception as e:
            self.logger.error('[RELATYPE.PUT] 更新RELATYPE失败: %s' % e)
            return 3
        else:
            if updateAttrType is None:
                return 3
            else:
                self.logger.info('[RELATYPE.PUT] 更新RELATYPE, FID=%s' % fid)
                return fid