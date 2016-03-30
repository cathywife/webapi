#!/usr/bin/python
#coding: utf-8
#print "Content-type: text/html\n" 
#Author: LIPH 
import web
import demjson
import json
import string
import time
import urlparse
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

render = web.template.render('templates/')

urls = ( '/cirelatype/(.*)', 'RELATYPE',
         '/cirelatype', 'relatype',  )

db = web.database(dbn='oracle', user='cmdb', pw='cmdb123', db='cffexcmdb')
#Define time stamp 9999/12/31 23:59:59
ENDTIME = str(int('99991231235959'))
DELETETIME = str('00000000000000')

def fn_create_ci_relatype(i_name,i_st_fid,i_tt_fid,i_owner,i_relation, i_family_id,i_change_log,i_displayname,i_endtime=ENDTIME):
    #Function：create ci
    v_crt = 'PCRT00000001'
    v_frt = 'FCRT00000001'
    ct_id = db.query('select max(id) cid, max(family_id) fid from t_ci_relation_type ')
    #Although there will be only one record, it also needs to iteratively generate the dict. It will raise an error if directly transforming ci_id[0] to json format
    ci_as_dict = []
    for ci in ct_id:
        ci_as_dict.append(ci)
    
    v_json = json.dumps(ci_as_dict).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    #Take the default value when inserting the first record
    if v_num <> 0 :
        v_crt = v_djson[0]['CID']
        v_frt = v_djson[0]['FID']
        v_crt = 'PCRT' + str(string.atoi(v_crt[4:])+1).rjust(8,'0')
        if i_family_id == None :
            v_frt = 'FCRT' + str(string.atoi(v_frt[4:])+1).rjust(8,'0')
        else:
            v_frt = i_family_id
    v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
    n = db.insert('t_ci_relation_type',id = v_crt,name = i_name, source_type_fid = i_st_fid, target_type_fid = i_tt_fid, 
                  owner = i_owner, starttime = v_curtime, endtime = i_endtime, relation = i_relation, family_id = v_frt, change_log = i_change_log,displayname = i_displayname)
    return v_frt

def fn_delete_ci_relatype(i_family_id,i_curtime,i_change_log):
    #Function: Delete ci relation type
    v_ct_fids = db.query("select t.name,convert(t.displayname,'utf8') displayname, t.source_type_fid,t.target_type_fid,t.owner,t.relation,t.family_id from t_ci_relation_type t where t.family_id=$fid and t.endtime=$endtime",vars={'endtime':ENDTIME,'fid':i_family_id})
    ci_as_dict = []
    for ci in v_ct_fids:
        ci_as_dict.append(ci)
    ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
    ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
    #delete the record    
    n = db.update('t_ci_relation_type', where='family_id = $fid and endtime = $endtime', vars={'fid':i_family_id,'endtime':ENDTIME}, endtime=i_curtime)
    #insert a new record and set the endtime=deletetime
    v_fid = fn_create_ci_relatype(ci_type_djson[0]['NAME'], ci_type_djson[0]['SOURCE_TYPE_FID'], ci_type_djson[0]['TARGET_TYPE_FID'], 
                                      ci_type_djson[0]['OWNER'],ci_type_djson[0]['RELATION'], ci_type_djson[0]['FAMILY_ID'], i_change_log,ci_type_djson[0]['DISPLAYNAME'],DELETETIME)        
    return n

class RELATYPE:

   def GET(self,fid):
       ci_attrtype = db.query("select a.name sourcename,b.name targetname,convert(a.displayname, 'utf8') sourcedisplayname,convert(b.displayname, 'utf8') targetdisplayname, t.name,convert(t.displayname,'utf8') displayname, t.source_type_fid,t.target_type_fid,t.owner,t.relation,t.family_id,t.change_log from t_ci_relation_type t, t_ci_type a, t_ci_type b where t.family_id=$fid and t.endtime=$endtime and t.source_type_fid=a.family_id and a.endtime=$endtime and t.target_type_fid=b.family_id and b.endtime=$endtime ",vars={'endtime':ENDTIME,'fid':fid})
       ci_as_dict = []
       for ci in ci_attrtype:
           ci_as_dict.append(ci)
       ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       return ci_type_json
   
class relatype:

   def GET(self):
       all_col = ('name','source_type_fid','target_type_fid','owner','relation','family_id','time','change_log','sourcename','targetname') 
       citype_input = web.input()
       condition = " "
       for col in range(len(all_col)):
           col_name = all_col[col]
           value = citype_input.get(col_name,None)
           if value <> None:
               if col_name == 'time' :
                   condition = condition + "t.starttime <= '" + value + "' and t.endtime > '" + value + "' and a.starttime <= '" + value + "' and a.endtime > '" + value + "' and b.starttime <= '" + value + "' and b.endtime > '" + value + "' and "
               elif col_name == 'sourcename':
                   condition = condition + "a.name = '" + value + "' and "
               elif col_name == 'targetname':
                   condition = condition + "b.name = '" + value + "' and "    
               else :
                   condition = condition + "t." + col_name + " = '" + value + "' and "
           if value == None and col_name == 'time':
               condition = condition + "t.endtime = '" + ENDTIME + "' and a.endtime = '" + ENDTIME + "' and b.endtime = '" + ENDTIME + "' and "
               
       
       v_sql = "select a.name sourcename,b.name targetname,convert(a.displayname, 'utf8') sourcedisplayname," \
               "convert(b.displayname, 'utf8') targetdisplayname, t.name,convert(t.displayname,'utf8') displayname, " \
               "t.source_type_fid,t.target_type_fid,t.owner,t.relation,t.family_id,t.change_log from t_ci_relation_type t, " \
               "t_ci_type a, t_ci_type b where " + condition + " t.source_type_fid=a.family_id and t.target_type_fid=b.family_id "
       ci_relatype = db.query(v_sql)
       ci_as_dict = []
       for ci in ci_relatype:
           ci_as_dict.append(ci)
       ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       
#        import sys,httplib, urllib
#        params = urllib.urlencode({'fid':'FCRT00000001','change_log':'test'})
#        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
#        con2  =   httplib.HTTPConnection("localhost:8080") 
#        con2.request("DELETE","/cirelatype",params,headers) 
#        con2.close()
       
       return ci_type_json
    
   def POST(self):
        citype_input = web.input()
        #Besides some fields in t_ci_relation_type, input parameters also include the "name" field in t_ci_type . One for source, and the other one for target
        v_ct_fids = db.query('SELECT distinct ct.family_id sfid, tct.family_id tfid FROM t_ci_type ct, t_ci_type tct WHERE ct.endtime = $endtime and ct.family_id = $ctsfid and tct.endtime = $endtime and tct.family_id = $cttfid',vars={'endtime':ENDTIME,'ctsfid':citype_input.get('source_citype_fid',None),'cttfid':citype_input.get('target_citype_fid',None)})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there is no relative family id in table T_CI_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one relative family ids in table T_CI_TYPE
        v_ct_sfid = json_de[0]['SFID']
        v_ct_tfid = json_de[0]['TFID']
                       
        #Users don't need to input the family_id . The afferent parameter for the function is null
        v_fid = fn_create_ci_relatype(citype_input.get('name',None), v_ct_sfid, v_ct_tfid, 
                      citype_input.get('owner',None), citype_input.get('relation',None), None, 'initialization', citype_input.get('displayname',None))
        
        return v_fid
    
   def DELETE(self):
        input_data = web.data()
        data = urlparse.parse_qs(input_data)        
        v_ct_fids = db.query("SELECT distinct c.name FROM t_ci_relation_type c WHERE  c.family_id = $fid and c.endtime = $endtime",vars={'fid':data['fid'][0],'endtime':ENDTIME})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there are no records to delete in table t_ci_relation_type
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to delete in table t_ci_relation_type
        #Before deleting t_ci_relation_type, we should ensure that there are no relative records in t_ci_relation
        v_num = db.query('select count(*) num from t_ci_relation a where a.type_fid = $fid and a.endtime = $endtime',vars={'fid':data['fid'][0],'endtime':ENDTIME})
        ci_at_num = v_num[0]['NUM']
        if ci_at_num <> 0:
            return 4 #there are relative records in t_ci_relation_type
        
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        #Notice: when deleting table t_ci_relation_type, there must be no relative records in t_ci_relation
        n = fn_delete_ci_relatype(data['fid'][0],v_curtime,data['change_log'][0])
        return n
    
   def PUT(self):
        citype_input = web.input()
        v_ct_fids = db.query("select t.name,convert(t.displayname,'utf8') displayname, t.source_type_fid,t.target_type_fid,t.owner,t.relation,t.family_id,t.change_log from t_ci_relation_type t where t.family_id=$fid and t.endtime=$endtime",vars={'endtime':ENDTIME,'fid':citype_input.get('fid',None)})
        ci_as_dict = []
        for ci in v_ct_fids:
           ci_as_dict.append(ci)
        ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
        ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
        v_ct_fid_num = len(ci_type_djson)
        if v_ct_fid_num == 0:
            return 2 #there are no records to modify in table t_ci_relation_type
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to modify in table t_ci_relation_type
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = db.update('t_ci_relation_type', where='family_id = $fid and endtime = $endtime', vars={'fid':citype_input.get('fid'),'endtime':ENDTIME}, endtime=v_curtime)
        v_fid = fn_create_ci_relatype(citype_input.get('name',ci_type_djson[0]['NAME']), ci_type_djson[0]['SOURCE_TYPE_FID'], ci_type_djson[0]['TARGET_TYPE_FID'], 
                                      citype_input.get('owner',ci_type_djson[0]['OWNER']),citype_input.get('relation',ci_type_djson[0]['RELATION']),
                                  ci_type_djson[0]['FAMILY_ID'], citype_input.get('change_log',ci_type_djson[0]['CHANGE_LOG']),citype_input.get('displayname',ci_type_djson[0]['DISPLAYNAME']))        
        return v_fid

if __name__ == "__main__":  
    app = web.application(urls, globals())
    app.run()
