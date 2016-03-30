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

import webci_attr
import webci_relation

reload(sys)
sys.setdefaultencoding('utf-8')

render = web.template.render('templates/')

urls = ( '/ci/(.*)', 'CI',
         '/ci', 'ci',
        )

db = web.database(dbn='oracle', user='cmdb', pw='cmdb123', db='cffexcmdb')
#Define time stamp 9999/12/31 23:59:59
ENDTIME = str(int('99991231235959'))
DELETETIME = str('00000000000000')

def fn_create_ci(i_name,i_description,i_tag,i_priority,i_owner,i_type_fid,i_family_id,i_change_log,i_endtime=ENDTIME):
    #Function: Create ci
    v_cid = 'PCID00000001'
    v_fid = 'FCID00000001'
    ci_id = db.query('select max(id) cid, max(family_id) fid from t_ci ')
    #Although there will be only one record, it also needs to iteratively generate the dict. It will raise an error if directly transforming ci_id[0] to json format
    ci_as_dict = []
    for ci in ci_id:
        ci_as_dict.append(ci)
    
    v_json = json.dumps(ci_as_dict).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    #Take the default value when inserting the first record
    if v_num <> 0 :
        v_cid = v_djson[0]['CID']
        v_fid = v_djson[0]['FID']
        v_cid = 'PCID' + str(string.atoi(v_cid[4:])+1).rjust(8,'0')
        if i_family_id == None :
            v_fid = 'FCID' + str(string.atoi(v_fid[4:])+1).rjust(8,'0')
        else:
            v_fid = i_family_id
    v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
    n = db.insert('t_ci',id = v_cid,name = i_name, description = i_description, tag = i_tag, priority = i_priority, 
                  owner = i_owner, starttime = v_curtime, endtime = i_endtime, type_fid = i_type_fid, family_id = v_fid, change_log = i_change_log)
    return v_fid

def fn_delete_ci(i_family_id,i_curtime,i_change_log):
    #Function，delete ci
    #Notice；besides t_ci，information in t_ci_attribute and t_ci_relation should be deleted too
    #delete t_ci_attribute
    family_id = db.query('select distinct a.family_id from t_ci_attribute a where a.ci_fid = $fid and a.endtime = $endtime',vars={'fid':i_family_id,'endtime':ENDTIME})
    family_ids = []
    for fid in family_id:
        family_ids.append(fid)
    v_json = json.dumps(family_ids).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    if v_num <> 0 :
        for fid in v_djson:
            n = webci_attr.fn_delete_ciattr(fid['FAMILY_ID'], i_curtime, i_change_log) 
    #delete t_ci_relation where the ci is the target
    family_id = db.query('select distinct a.family_id from t_ci_relation a where a.target_fid = $fid and a.endtime = $endtime',vars={'fid':i_family_id,'endtime':ENDTIME})
    family_ids = []
    for fid in family_id:
        family_ids.append(fid)
    v_json = json.dumps(family_ids).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    if v_num <> 0 :
        for fid in v_djson:
            n = webci_relation.fn_delete_cirela(fid['FAMILY_ID'], i_curtime, i_change_log)
    #delete the target ci where the ci is the source
    family_id = db.query("select distinct b.family_id, b.target_fid from t_ci a,t_ci_relation b,t_ci_relation_type c where a.family_id=$fid and a.family_id=b.source_fid and b.type_fid=c.family_id and c.relation='COMPOSITION' and b.endtime=$endtime and c.endtime=$endtime",vars={'fid':i_family_id,'endtime':ENDTIME})
    family_ids = []
    for fid in family_id:
        family_ids.append(fid)
    v_json = json.dumps(family_ids).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    if v_num <> 0 :
        for fid in v_djson:
            fn_delete_ci(fid['TARGET_FID'],i_curtime, i_change_log)
            #In the ci delete function, it will delete the relative relation record which including the target ci_id, thus, there is no need to delete the t_ci_relation again 
    
    #delete t_ci_relation where the ci is the source
    family_id = db.query('select distinct a.family_id from t_ci_relation a where a.source_fid = $fid and a.endtime = $endtime',vars={'fid':i_family_id,'endtime':ENDTIME})
    family_ids = []
    for fid in family_id:
        family_ids.append(fid)
    v_json = json.dumps(family_ids).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    if v_num <> 0 :
        for fid in v_djson:
            n = webci_relation.fn_delete_cirela(fid['FAMILY_ID'], i_curtime, i_change_log)
    #Prepare to delete ci
    v_ct_fids = db.query("SELECT c.name,convert(c.description,'utf8') description,c.tag,c.priority,c.owner,c.type_fid,c.family_id FROM t_ci c WHERE c.endtime = $endtime and c.family_id = $fid",vars={'endtime':ENDTIME,'fid':i_family_id})
    ci_as_dict = []
    for ci in v_ct_fids:
        ci_as_dict.append(ci)
    ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
    ci_type_djson = json.loads(ci_type_json,encoding="gb2312")    
    #delete t_ci
    n = db.update('t_ci', where='family_id = $fid and endtime = $endtime', vars={'fid':i_family_id,'endtime':ENDTIME}, endtime=i_curtime)
    #insert a new record and  set the endtime=deletetime
    v_fid = fn_create_ci(ci_type_djson[0]['NAME'], ci_type_djson[0]['DESCRIPTION'], ci_type_djson[0]['TAG'], ci_type_djson[0]['PRIORITY'],
                      ci_type_djson[0]['OWNER'], ci_type_djson[0]['TYPE_FID'], ci_type_djson[0]['FAMILY_ID'], i_change_log,DELETETIME)     
    return n    

class CI:

   def GET(self,fid):
       ci_rec = db.query("select distinct a.name citype_name, convert(a.displayname,'utf8') type_displayname, b.name,convert(b.description,'utf8') description,b.tag,b.priority,b.owner,b.type_fid,b.family_id,b.change_log from t_ci b, t_ci_type a where b.endtime = $endtime and a.endtime = $endtime and a.family_id=b.type_fid and b.family_id = $fid ",vars={'endtime':ENDTIME,'fid':fid})
       ci_as_dict = []
       for ci in ci_rec:
           ci_as_dict.append(ci)
       ci_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       return ci_json
   
class ci:

   def GET(self):
       #all_col = db.query('select lower(t.column_name) column_name from dba_col_comments t where t.owner=$owner and t.table_name=$tablename',vars={'owner':'CMDB','tablename':'T_CI'})
#        ci_input = web.input(name = None)
       all_col = ('name','description','tag','owner','type_fid','family_id','priority','time','change_log','citype_name') 
       ci_input = web.input()
       condition = " "
       for col in range(len(all_col)):
           col_name = all_col[col]
           value = ci_input.get(col_name,None)
           if value <> None:
               if col_name == 'time' :
                   condition = condition + "b.starttime <= '" + value + "' and b.endtime > '" + value + "' and a.starttime <= '" + value + "' and a.endtime > '" + value + "' and "
               elif col_name == 'citype_name' :
                   condition = condition + "a.name = '" + value + "' and "
               else :
                   condition = condition + "b." + col_name + " = '" + value + "' and "
           if value == None and col_name == 'time':
               condition = condition + "b.endtime = '" + ENDTIME + "' and a.endtime = '" + ENDTIME + "' and "
               
       v_sql = "select distinct a.name citype_name, convert(a.displayname,'utf8') type_displayname, b.name,convert(b.description,'utf8') description,b.tag,b.priority,b.owner,b.type_fid,b.family_id,b.change_log from t_ci b, t_ci_type a where " + condition + "a.family_id=b.type_fid"
       ci_recs = db.query(v_sql)
       ci_as_dict = []
       for ci in ci_recs:
           ci_as_dict.append(ci)
       ci_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       
#        import sys,httplib, urllib 
#        params = urllib.urlencode({'fid':'FCID00000004','change_log':'test'})
#        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
#        con2  =   httplib.HTTPConnection("localhost:8080") 
#        con2.request("DELETE","/ci",params,headers) 
#        con2.close()

       return ci_json
       
   def POST(self):
        ci_input = web.input()
        #Besides some fields in t_ci, input parameters also include the "name" field in t_ci_type 
        v_ct_fids = db.query('SELECT distinct ct.family_id FROM t_ci_type ct WHERE ct.endtime = $endtime and ct.family_id = $ctfid',vars={'endtime':ENDTIME,'ctfid':ci_input.get('ci_type_fid',None)})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there is no relative family id in table T_CI_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one relative family ids in table T_CI_TYPE
        v_ct_fid = json_de[0]['FAMILY_ID']
        
        #Users don't need to input the family_id . The afferent parameter for the function is null
        v_fid = fn_create_ci(ci_input.get('name',None), ci_input.get('description',None), ci_input.get('tag',None), ci_input.get('priority',0),
                      ci_input.get('owner',None), v_ct_fid, None, 'initialization')
        return v_fid

   def DELETE(self):
        input_data = web.data()
        data = urlparse.parse_qs(input_data)
        v_ct_fids = db.query('SELECT distinct c.name FROM t_ci c WHERE  c.family_id = $fid and c.endtime=$endtime',vars={'fid':data['fid'][0],'endtime':ENDTIME})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there are no records to delete in table t_ci
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to delete in table t_ci
        #Notice；besides t_ci，information in t_ci_attribute and t_ci_relation should be deleted too
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = fn_delete_ci(data['fid'][0],v_curtime,data['change_log'][0])
        return n
    
   def PUT(self):
        ci_input = web.input()
        v_ct_fids = db.query("SELECT c.name,convert(c.description,'utf8') description,c.tag,c.priority,c.owner,c.type_fid,c.family_id,c.change_log FROM t_ci c WHERE c.endtime = $endtime and c.family_id = $fid",vars={'endtime':ENDTIME,'fid':ci_input.get('fid',None)})
        ci_as_dict = []
        for ci in v_ct_fids:
           ci_as_dict.append(ci)
        ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
        ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
        v_ct_fid_num = len(ci_type_djson)

        if v_ct_fid_num == 0:
            return 2 #there are no records to modify in table t_ci
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to modify in table t_ci
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = db.update('t_ci', where='family_id = $fid and endtime = $endtime', vars={'fid':ci_input.get('fid'),'endtime':ENDTIME}, endtime=v_curtime)
        v_fid = fn_create_ci(ci_input.get('name',ci_type_djson[0]['NAME']), ci_input.get('description',ci_type_djson[0]['DESCRIPTION']), ci_input.get('tag',ci_type_djson[0]['TAG']), ci_input.get('priority',ci_type_djson[0]['PRIORITY']),
                      ci_input.get('owner',ci_type_djson[0]['OWNER']), ci_type_djson[0]['TYPE_FID'], ci_type_djson[0]['FAMILY_ID'], ci_input.get('change_log',ci_type_djson[0]['CHANGE_LOG']))
        return v_fid
    

if __name__ == "__main__":  
    app = web.application(urls, globals())
    app.run()
