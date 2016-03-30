#!/usr/bin/python
#coding: utf-8
#print "Content-type: text/html\n"
#Author: LIPH
import json
import string
import sys
import time
import urlparse

import demjson
import web

import webci_attr_type
import webci_relation_type

reload(sys)
sys.setdefaultencoding('utf-8')

render = web.template.render('templates/')

urls = ( '/citype/(.*)', 'CITYPE',
         '/citype', 'citype',  )

db = web.database(dbn='oracle', user='cmdb', pw='cmdb123', db='cffexcmdb')
#Define time stamp 9999/12/31 23:59:59
ENDTIME = str(int('99991231235959'))
DELETETIME = str('00000000000000')

def fn_create_ci_type(i_name,i_description,i_owner,i_family_id,i_change_log,i_displayname,i_endtime=ENDTIME):
    #Function：create ci type
    v_cit = 'PCIT00000001'
    v_fit = 'FCIT00000001'
    ct_id = db.query('select max(id) cid, max(family_id) fid from t_ci_type ')
    #Although there will be only one record, it also needs to iteratively generate the dict. It will raise an error if directly transforming ci_id[0] to json format
    ci_as_dict = []
    for ci in ct_id:
        ci_as_dict.append(ci)

    v_json = json.dumps(ci_as_dict).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    #Take the default value when inserting the first record
    if v_num <> 0 :
        v_cit = v_djson[0]['CID']
        v_fit = v_djson[0]['FID']
        v_cit = 'PCIT' + str(string.atoi(v_cit[4:])+1).rjust(8,'0')
        if i_family_id == None :
            v_fit = 'FCIT' + str(string.atoi(v_fit[4:])+1).rjust(8,'0')
        else:
            v_fit = i_family_id
    v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
    n = db.insert('t_ci_type',id = v_cit,name = i_name, description = i_description,
                  owner = i_owner, starttime = v_curtime, endtime = i_endtime, family_id = v_fit, change_log = i_change_log,displayname = i_displayname)
    return v_fit

def fn_delete_ci_type(i_family_id,i_curtime,i_change_log):
    v_ct_fids = db.query("SELECT ct.name ,convert(ct.description,'utf8') description,ct.owner,ct.family_id,convert(ct.displayname,'utf8') displayname from t_ci_type ct WHERE ct.endtime = $endtime and  ct.family_id = $fid",vars={'endtime':ENDTIME,'fid':i_family_id})
    ci_as_dict = []
    for ci in v_ct_fids:
        ci_as_dict.append(ci)
    ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
    ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
    #delete the record
    n = db.update('t_ci_type', where='family_id = $fid and endtime = $endtime', vars={'fid':i_family_id,'endtime':ENDTIME}, endtime=i_curtime)
    #insert a new record and set the endtime=deletetime
    v_fid = fn_create_ci_type(ci_type_djson[0]['NAME'],ci_type_djson[0]['DESCRIPTION'], ci_type_djson[0]['OWNER'],
                                 ci_type_djson[0]['FAMILY_ID'], i_change_log,ci_type_djson[0]['DISPLAYNAME'],DELETETIME)
    return n

class CITYPE:

   def GET(self,fid):
       ci_type = db.query("select a.name ,convert(a.description,'utf8') description,a.owner,a.family_id,convert(a.displayname,'utf8') displayname,a.change_log from t_ci_type a where a.endtime = $aendtime and a.family_id = $fid ",vars={'aendtime':ENDTIME,'fid':fid})
       ci_as_dict = []
       for ci in ci_type:
           ci_as_dict.append(ci)
#        type_ci = ci_type[0]
#        print type(type_ci)
#        print type_ci.DISPLAYNAME.decode('utf-8')
#        print type_ci.DESCRIPTION.decode('utf-8')
#        ci_type_json = demjson.encode(type_ci,encoding='UTF-8' )
#        print ci_type_json
#        ci_type_djson = demjson.decode(ci_type_json)
#        print ci_type_djson
       ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       return ci_type_json

class citype:

   def GET(self):
       all_col = ('name','description','owner','family_id','time','change_log')
       citype_input = web.input()
       condition = " "
       for col in range(len(all_col)):
           col_name = all_col[col]
           value = citype_input.get(col_name,None)
           if value <> None:
               if col_name == 'time' :
                   condition = condition + "ct.starttime <= '" + value + "' and ct.endtime > '" + value + "' and "
               else :
                   condition = condition + "ct." + col_name + " = '" + value + "' and "
           if value == None and col_name == 'time':
               condition = condition + "ct.endtime = '" + ENDTIME + "' and "

       v_sql = "select ct.name , convert(ct.description,'utf8') description,ct.owner,ct.family_id,convert(ct.displayname,'utf8') " \
               "displayname,ct.change_log from t_ci_type ct where " + condition + "1=1"
       #v_sql = "select ct.name , ct.description,ct.owner,ct.family_id,ct.displayname,ct.change_log from t_ci_type ct where " + condition + "1=1"
       ci_type = db.query(v_sql)
       ci_as_dict = []
       for ci in ci_type:
           ci_as_dict.append(ci)
       ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       #Type is unicode
#        import sys,httplib, urllib
#        params = urllib.urlencode({'fid':'FCIT00000004','change_log':'test'})
#        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
#        con2  =   httplib.HTTPConnection("localhost:8080")
#        con2.request("DELETE","/citype",params,headers)
#        con2.close()

       return ci_type_json

   def POST(self):
        citype_input = web.input()
        #Users don't need to input the family_id . The afferent parameter for the function is null
        v_fid = fn_create_ci_type(citype_input.get('name',None), citype_input.get('description',None),
                      citype_input.get('owner',None), None, 'initialization', citype_input.get('displayname',None))
        return v_fid

   def DELETE(self):
        input_data = web.data()
        data = urlparse.parse_qs(input_data)
        v_ct_fids = db.query("SELECT distinct c.name FROM t_ci_type c WHERE  c.family_id = $fid and c.endtime = $endtime",
                             vars={'fid':data['fid'][0],'endtime':ENDTIME})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there are no records to delete in table T_CI_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to delete in table T_CI_TYPE
        #Before deleting t_ci_type, we should ensure that there are no relative records in t_ci、t_ci_attribute_type、t_ci_relation_type
        v_num = db.query('select count(*) num from t_ci a where a.type_fid = $fid and a.endtime = $endtime',vars={'fid':data['fid'][0],'endtime':ENDTIME})
        ci_num = v_num[0]['NUM']
        if ci_num <> 0:
            return 4 #there are relative records in t_ci
        # If there is no relative ci, there will be no relative attribute and relation. Then we can directly delete attribute type and relation type
        # Delete ci_attribute_type
        v_cat_fids = db.query('select distinct a.family_id from t_ci_attribute_type a where a.ci_type_fid = $fid and a.endtime = $endtime',vars={'fid':data['fid'][0],'endtime':ENDTIME})
        json_en = demjson.encode(v_cat_fids)
        json_de = demjson.decode(json_en)
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num <> 0:
            for v_cat_fid in json_de:
                n = webci_attr_type.fn_delete_ci_attrtype(v_cat_fid['FAMILY_ID'], v_curtime, data['change_log'][0])
        #Delete ci_relation_type
        v_crt_fids = db.query('select distinct a.family_id from t_ci_relation_type a where (a.source_type_fid = $fid or a.target_type_fid = $fid) and a.endtime = $endtime',vars={'fid':data['fid'][0],'endtime':ENDTIME})
        json_en = demjson.encode(v_crt_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num <> 0:
            for v_crt_fid in json_de:
                n = webci_relation_type.fn_delete_ci_relatype(v_crt_fid['FAMILY_ID'], v_curtime, data['change_log'][0])

        #Delete t_ci_type
        n = fn_delete_ci_type(data['fid'][0],v_curtime,data['change_log'][0])
        return n

   def PUT(self):
        citype_input = web.input()
        v_ct_fids = db.query("SELECT ct.name ,convert(ct.description,'utf8') description,ct.owner,ct.family_id,"
                             "convert(ct.displayname,'utf8') displayname,ct.change_log from t_ci_type ct "
                             "WHERE ct.endtime = $endtime and  ct.family_id = $fid",vars={'endtime':ENDTIME,'fid':citype_input.get('fid',None)})
        ci_as_dict = []
        for ci in v_ct_fids:
           ci_as_dict.append(ci)
        ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
        ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
        v_ct_fid_num = len(ci_type_djson)
        if v_ct_fid_num == 0:
            return 2 #there are no relative records to modify in table T_CI_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to modify in table T_CI_TYPE
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = db.update('t_ci_type', where='family_id = $fid and endtime = $endtime', vars={'fid':citype_input.get('fid'),'endtime':ENDTIME}, endtime=v_curtime)
        v_fid = fn_create_ci_type(citype_input.get('name',ci_type_djson[0]['NAME']), citype_input.get('description',ci_type_djson[0]['DESCRIPTION']), citype_input.get('owner',ci_type_djson[0]['OWNER']),
                                  citype_input.get('fid',ci_type_djson[0]['FAMILY_ID']), citype_input.get('change_log',ci_type_djson[0]['CHANGE_LOG']),citype_input.get('displayname',ci_type_djson[0]['DISPLAYNAME']))
        return v_fid

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
