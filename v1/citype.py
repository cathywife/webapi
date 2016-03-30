# -*- coding: utf-8 -*-

import json
import logging
import sys

import web

from common.ID import ID
from common.Time import Time

reload(sys)
sys.setdefaultencoding('utf-8')

class citype:
    def __init__(self):
        self.db = web.database(dbn='oracle', user='cap', pw='cap_1234', db='oracapdb')
        self.id = ID()
        self.time = Time()
        self.logger = logging.getLogger('cmdbapi')

    def createCIType(self, id, fid, name, displayname, description, owner, log, starttime, endtime):
        '''
        创建CITYPE
        :param id:
        :param fid:
        :param name:
        :param description:
        :param displayname:
        :param owner:
        :param log:
        :param starttime:
        :param endtime:
        :return: 如果插入成功，返回FID；如果插入失败，返回NONE
        '''
        if id is None or fid is None or name is None or displayname is None or \
           starttime is None or endtime is None:
            self.logger.error('[CITYPE.CREATECITYPE] 创建CITYPE[ID:%S, FID:%S]失败: 参数[ID|FID|NAME|DISPLAYNAME'
                              '|STARTTIME|ENDTIME]不可为空.' % (id, fid))
            return None

        try:
            result = self.db.insert('T_CITYPE', id=id, fid=fid, name=name, displayname=displayname,
                                    description=description, owner=owner, log=log, starttime=starttime,
                                    endtime=endtime)
        except Exception as e:
            self.logger.error('[CITYPE.CREATECITYPE] 创建CITYPE[ID:%S, FID:%S]失败: %s.' % (id, fid, e))
        else:
            return fid

    def deleteCIType(self, fid, currentTime, log):
        '''
        删除CITYPE
        :param fid: CIType对应的Family ID
        :param currentTime: 删除CIType时输入的当前时间
        :param log: CIType中log字段的值
        :return:
        '''
        if fid is None or currentTime is None:
            self.logger.error('FID或者当前时间字段为空，无法删除CITYPE记录')
            return False

        try:
            citype = self.db.query("T_CITYPE", where='endtime = $endtime and fid = $fid',
                              vars={'endtime':ENDTIME, 'fid':fid})
            # 将citype的endtime字段更新为当前时间
            self.db.update('T_CITYPE', where='fid=$fid and endtime=$endtime',
                      vars={'fid':fid,'endtime':ENDTIME}, endtime=currentTime)
            if len(citype) <> 1:
                self.logger.error('查询出的CITYPE记录不唯一')
                return False
        except Exception as e:
            self.logger.error('查询或者更新CITYPE失败，%s', e)
            return False

        deleteResult = self.createCIType(citype[0]['ID'], citype[0]['FID'], citype[0]['NAME'],
                          citype[0]['DESCRIPTION'], citype[0]['DISPLAYNAME'],citype[0]['OWNER'],
                          log, currentTime, DELETETIME)
        if deleteResult == fid:
            return True
        else:
            self.logger.error('删除CITYPE出错')
            return False

    def GET(self):
        '''
        GET方法，实现API查询
        :return: 1：执行查询语句时失败
                 json格式文本：查询成功，返回查找出的数据
        '''
        result = web.input()
        params = {
            'id': result.get('id'),
            'fid': result.get('fid'),
            'name': result.get('name'),
            'displayname': result.get('displayname'),
            'owner': result.get('owner'),
            'time': result.get('time'),
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
            queryResult = self.db.query('SELECT * FROM T_CITYPE where ' + conditions)
            citypeList = []
            for each in queryResult:
                citypeList.append(each)
        except Exception as e:
            self.logger.error('[CITYPE.GET] 查询CITYPE失败: %s' % e)
            return 1
        else:
            self.logger.info('[CITYPE.GET] 查询CITYPE, 条件为: %s' % conditions)

        return json.dumps(citypeList, indent=2, ensure_ascii=False, separators=(',', ':')).decode('utf-8')

    def POST(self):
        '''
        POST方法，实现API插入操作
        :return: 1：生成主键ID或者组ID失败
                 2：调用createCITYPE函数创建CI，返回值为None，表示插入失败
                 fid：插入成功，返回组ID
        '''
        result = web.input(name=None, displayname=None, description=None, owner=None, log=None)
        params = {
            'name':result.get('name'),
            'displayname':result.get('displayname'),
            'description':result.get('description'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }

        id = self.id.getCITypeID()
        fid = self.id.getCITypeFid()
        if id is None or fid is None:
            self.logger.error("[CITYPE.POST] 获取ID和FID失败")
            return 1

        starttime = self.time.getNow()
        endtime = self.time.getEndTime()
        citype = self.createCIType(id=id, fid=fid, name=params['name'], displayname=params['displayname'],
                                   description=params['description'], owner=params['owner'],
                                   log=params['log'], starttime=starttime, endtime=endtime)
        if citype is None:
            return 2
        else:
            self.logger.info("[CITYPE.POST] 创建CITYPE[ID:%s，FID:%s]" % (id, fid))
            return fid

    def PUT(self):
        '''
        PUT方法，实现API更新操作
        :return: 1：输入的参数fid为空
                 2：查询指定fid和endtime的citype时出错
                 3. 查询获得的citype记录不为1
                 4. 更新citype的endtime字段失败
                 5. 插入citype记录失败
                 fid：更新操作执行成功
        '''
        result = web.input()
        params = {
            'fid':result.get('fid'),
            'name':result.get('name'),
            'displayname':result.get('displayname'),
            'description':result.get('description'),
            'owner':result.get('owner'),
            'log':result.get('log'),
        }
        fid = params['fid']
        if fid is None:
            self.logger.error("[CITYPE.PUT] 更新CITYPE失败: 输入参数FID为空")
            return 1
        elif params.values().count(not None) == 1:
            self.logger.error("[CITYPE.PUT] 更新CITYPE失败: 无待更新字段")
            return 1

        try:
            endtime = self.time.getEndTime()
            try:
                citype = self.db.query("SELECT * FROM T_CITYPE WHERE endtime = $endtime and fid = $fid",
                              vars={'endtime':endtime, 'fid':fid})
                citype=list(citype)
            except Exception as e:
                self.logger.error('[CITYPE.PUT] 更新CITYPE失败: 查找FID=%s的CITYPE项失败. %s' % (fid, e))
                return 2
            else:
                if len(citype) <> 1:
                    self.logger.error('[CITYPE.PUT] 更新CITYPE失败: 查找FID=%s, endtime=%s的CITYPE不唯一' %
                                      (fid, endtime))
                    return 2

            params = {
                'name':result.get('name', citype[0]['NAME']),
                'displayname':result.get('displayname', citype[0]['DISPLAYNAME']),
                'description':result.get('description', citype[0]['DESCRIPTION']),
                'owner':result.get('owner', citype[0]['OWNER']),
                'log':result.get('log', citype[0]['LOG']),
            }

            updatetime = self.time.getNow()
            n = self.db.update('T_CITYPE', where='fid = $fid and endtime = $endtime',
                      vars={'fid':fid, 'endtime': endtime}, endtime=updatetime)

            if n <> 1:
                self.logger.error("[RELATYPE.PUT] 更新RELATYPE失败: 更新记录ENDTIME字段失败")
                return 2

            id = self.id.getCITypeID()
            if id is None:
                self.logger.error("[CITYPE.PUT] 更新CITYPE失败: 生成ID失败")
                return 2
            updateCIType = self.createCIType(id=id, fid=fid, name=params['name'], displayname=params['displayname'],
                                            description=params['description'], owner=params['owner'],
                                            log=params['log'], starttime=updatetime, endtime=endtime)
        except Exception as e:
            self.logger.error('[CITYPE.PUT] 更新CITYPE失败: %s' % e)
            return 3
        else:
            if updateCIType is None:
                return 3
            else:
                self.logger.info('[CITYPE.PUT] 更新CITYPE, FID=%s' % fid)
                return fid

    def DELETE(self):
        '''
        删除CITYPE
        :return: 1：输入的参数存在不正确
                 2：查询CITYPE和CI时，查询语句报错
                 3：无法查询出匹配的CI TYPE
                 4：查询出存在CI，无法进行删除操作
                 5：ATTR TYPE删除失败
                 6：CITYPE删除失败
                 0：删除CITYPE成功
        '''
        print '1'
        result = web.input(fid=None,
                           log=None)
        # 无输入参数
        if result.fid == None:
            print 'shit'
            return 1
        print result.fid
        try:
            CITypeItems = self.db.query("SELECT count(name) num FROM T_CITYPE WHERE fid = $fid and endtime = $endtime",
                                vars={'fid':result.fid, 'endtime':ENDTIME})
            CIItems = self.db.query('select count(*) num from T_CI a where type_fid = $fid and endtime = $endtime',
                            vars={'fid':result.fid ,'endtime':ENDTIME})
        except Exception as e:
            self.logger.error('查询CITYPE及CITYPE对应的CI出错')
            return 2
        else:
            if CITypeItems[0]['num'] <> 1: # 没有找到匹配的CI TYPE
                self.logger.error('查找FID=%s的CITYPE条目不为1', result.fid)
                return 3
            elif CIItems[0]['num'] <> 0:    # 对应词CI TPYE的CI配置项还存在，无法直接删除该CI TYPE
                self.logger.error('CITYPE对应的CI配置项不为空，无法进行删除')
                return 4
        print '1'
        try:
            attrtype = self.db.query('select distinct fid from T_ATTRTYPE where citype_fid = $fid and endtime = $endtime',
                            vars={'fid':result.fid,'endtime':ENDTIME})
        except Exception as e:
            self.logger.error('查询CITYPE包含的ATTRTYPE出错, %s', e)
            return 2

        currentTime = self.getCurrentTime()
        for each in attrtype:
            retDelAttrType = attrtype.deleteAttrType(each['FID'], currentTime, result.log)
            if retDelAttrType == False:
                self.logger.error('删除ATTRTYPE[FID:%s]失败', each['FID'])
                return 5

        retDelCIType = self.deleteCIType(result.fid, currentTime, result.get('log', '删除CITYPE'))
        if retDelCIType == False:
            self.logger.error('删除CITYPE[FID:%s]失败', result.fid)
            return 6
        else:
            return 0



