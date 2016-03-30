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

reload(sys)
sys.setdefaultencoding('utf-8')
import webci
render = web.template.render('templates/')

urls = ( '/cirela/(.*)', 'RELA',
         '/cirela', 'rela',  )

db = web.database(dbn='oracle', user='cmdb', pw='cmdb123', db='cffexcmdb')
#Define time stamp 9999/12/31 23:59:59
ENDTIME = str(int('99991231235959'))
DELETETIME = str('00000000000000')

def fn_create_cirela(i_source_fid,i_target_fid,i_type_fid,i_owner,i_family_id,i_change_log,i_endtime=ENDTIME):    
    #Function：create ci_relation
    v_crd = 'PCRD00000001'
    v_frd = 'FCRD00000001'
    ci_id = db.query('select max(id) cad, max(family_id) fad from t_ci_relation ')
    #Although there will be only one record, it also needs to iteratively generate the dict. It will raise an error if directly transforming ci_id[0] to json format
    ci_as_dict = []
    for ci in ci_id:
        ci_as_dict.append(ci)
    
    v_json = json.dumps(ci_as_dict).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    #Take the default value when inserting the first record
    if v_num <> 0 :
        v_crd = v_djson[0]['CAD']
        v_frd = v_djson[0]['FAD']
        v_crd = 'PCRD' + str(string.atoi(v_crd[4:])+1).rjust(8,'0')
        if i_family_id == None :
            v_frd = 'FCRD' + str(string.atoi(v_frd[4:])+1).rjust(8,'0')
        else:
            v_frd = i_family_id
    v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
    n = db.insert('t_ci_relation',id = v_crd,source_fid = i_source_fid, target_fid = i_target_fid, type_fid = i_type_fid, 
                  owner = i_owner, starttime = v_curtime, endtime = i_endtime, family_id = v_frd, change_log = i_change_log)
    return v_frd

def fn_delete_cirela(i_family_id,i_curtime,i_change_log):
    v_ct_fids = db.query("select distinct t.source_fid,t.target_fid,t.type_fid,t.owner,t.family_id from t_ci_relation t where t.family_id=$fid and t.endtime=$endtime",vars={'endtime':ENDTIME,'fid':i_family_id})
    json_en = demjson.encode(v_ct_fids)
    json_de = demjson.decode(json_en)
    #delete the record
    n = db.update('t_ci_relation', where='family_id = $fid and endtime = $endtime', vars={'fid':i_family_id,'endtime':ENDTIME}, endtime=i_curtime)
    #insert a new record and set the endtime=deletetime
    v_fid = fn_create_cirela(json_de[0]['SOURCE_FID'],json_de[0]['TARGET_FID'], json_de[0]['TYPE_FID'], json_de[0]['OWNER'], json_de[0]['FAMILY_ID'], i_change_log,DELETETIME)
    return n

class RELA:

   def GET(self,fid):
       ci_rec = db.query("select distinct a.name typename, b.name sourcename,b.type_fid source_type_fid, c.name targetname, c.type_fid target_type_fid, c.name targetname, t.source_fid, t.target_fid, t.type_fid,t.owner,t.family_id,t.change_log from t_ci_relation t , t_ci_relation_type a, t_ci b, t_ci c where t.family_id=$fid and t.type_fid=a.family_id and t.source_fid=b.family_id and t.target_fid=c.family_id and t.endtime=$endtime and a.endtime=$endtime and b.endtime=$endtime and c.endtime=$endtime",vars={'endtime':ENDTIME,'fid':fid})
       ci_as_dict = []
       for ci in ci_rec:
           ci_as_dict.append(ci)
       ci_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       return ci_json
   
class rela:

   def GET(self):
       all_col = ('source_fid','target_fid','type_fid','owner','family_id','time','change_log','typename','sourcename','targetname','source_type_fid','target_type_fid') 
       ci_input = web.input()
       condition = " "
       for col in range(len(all_col)):
           col_name = all_col[col]
           value = ci_input.get(col_name,None)
           if value <> None:
               if col_name == 'time' :
                   condition = condition + "t.starttime <= '" + value + "' and t.endtime > '" + value + "' and a.starttime <= '" + value + "' and a.endtime > '" + value + "' and b.starttime <= '" + value + "' and b.endtime > '" + value + "' and c.starttime <= '" + value + "' and c.endtime > '" + value + "' and "
               elif col_name == 'typename':
                   condition = condition + "a.name = '" + value + "' and "
               elif col_name == 'sourcename':
                   condition = condition + "b.name = '" + value + "' and "
               elif col_name == 'targetname':
                   condition = condition + "c.name = '" + value + "' and "
               elif col_name == 'source_type_fid':
                   condition = condition + "b.type_fid = '" + value + "' and "
               elif col_name == 'target_type_fid':
                   condition = condition + "c.type_fid = '" + value + "' and "
               else :
                   condition = condition + "t." + col_name + " = '" + value + "' and "
           if value == None and col_name == 'time':
               condition = condition + "t.endtime = '" + ENDTIME + "' and a.endtime = '" + ENDTIME + "' and b.endtime = '" + ENDTIME + "' and c.endtime = '" + ENDTIME + "' and "
               
       v_sql = "select distinct a.name typename, b.name sourcename, b.type_fid source_type_fid, c.name targetname, c.type_fid target_type_fid, t.source_fid, t.target_fid, t.type_fid,t.owner,t.family_id,t.change_log from t_ci_relation t , t_ci_relation_type a, t_ci b, t_ci c where " + condition + "t.type_fid=a.family_id and t.source_fid=b.family_id and t.target_fid=c.family_id " 
       ci_recs = db.query(v_sql)
       ci_as_dict = []
       for ci in ci_recs:
           ci_as_dict.append(ci)
       ci_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       
#        import sys,httplib, urllib 
#        params = urllib.urlencode({'fid':'FCRD00000001','change_log':'test'})
#        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
#        con2  =   httplib.HTTPConnection("localhost:8080") 
#        con2.request("DELETE","/cirela",params,headers) 
#        con2.close()

       return ci_json
       
   def POST(self):
        ci_input = web.input()
        #Besides some fields in t_ci_relation, input parameters also include the "name" field in t_ci and t_ci_relation_type
        v_ct_fids = db.query('select distinct a.family_id type_fid, b.family_id sfid, c.family_id tfid from t_ci_relation_type a, t_ci b, t_ci c where a.relation = $relation and b.family_id = $source_fid and c.family_id = $target_fid and a.source_type_fid = b.type_fid and a.target_type_fid = c.type_fid and a.endtime=$endtime and b.endtime=$endtime and c.endtime=$endtime',vars={'endtime':ENDTIME,'relation':ci_input.get('relation',None),'source_fid':ci_input.get('source_fid',None),'target_fid':ci_input.get('target_fid',None)})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there is no relative family_id in table T_CI and T_CI_RELATION_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one relative family_ids in table T_CI and T_CI_RELATION_TYPE
        v_sci_fid = json_de[0]['SFID']
        v_tci_fid = json_de[0]['TFID']
        v_cirela_fid = json_de[0]['TYPE_FID']
        
        
        v_fid = fn_create_cirela(v_sci_fid, v_tci_fid,v_cirela_fid,
                      ci_input.get('owner',None), None, 'initialization')
        return v_fid

   def DELETE(self):
        input_data = web.data()
        data = urlparse.parse_qs(input_data)
        v_ct_fids = db.query("select distinct t.source_fid,t.target_fid,t.type_fid,t.owner,t.family_id from t_ci_relation t where t.family_id=$fid and t.endtime=$endtime",vars={'endtime':ENDTIME,'fid':data['fid'][0]})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there is no records to delete in table T_CI_RELATION
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to delete in table T_CI_RELATION
        
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        #Notice；if the relation is composition and the target ci exists, we should delete the relative ci
        v_target_fids = db.query("select t.family_id, crt.relation from t_ci t, t_ci_relation_type crt where t.family_id=$target_fid and t.endtime=$endtime and crt.family_id=$type_fid and crt.endtime=$endtime and crt.relation='COMPOSITION'",vars={'endtime':ENDTIME,'target_fid':json_de[0]['TARGET_FID'],'type_fid':json_de[0]['TYPE_FID']})
        target_json_en = demjson.encode(v_target_fids)
        target_json_de = demjson.decode(target_json_en)
        v_target_num = len(target_json_de)
        if v_target_num <> 0:
            #delete the existed ci. It will also delete the relative ci_attribute and ci_relation.
            n = webci.fn_delete_ci(json_de[0]['TARGET_FID'], v_curtime, data['change_log'][0])
        else:
            #delete t_ci_relation
            n = fn_delete_cirela(data['fid'][0],v_curtime,data['change_log'][0])
        
        return n
    
   def PUT(self):
        ci_input = web.input()
        v_ct_fids = db.query("select distinct t.source_fid, t.target_fid, t.type_fid,t.owner,t.family_id,t.change_log from t_ci_relation t where t.family_id=$fid and t.endtime=$endtime",vars={'endtime':ENDTIME,'fid':ci_input.get('fid',None)})
        ci_as_dict = []
        for ci in v_ct_fids:
           ci_as_dict.append(ci)
        ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
        ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
        v_ct_fid_num = len(ci_type_djson)

        if v_ct_fid_num == 0:
            return 2 #there is no records to modify in table T_CI_RELATION
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to modify in table T_CI_RELATION
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = db.update('t_ci_relation', where='family_id = $fid and endtime = $endtime', vars={'fid':ci_input.get('fid'),'endtime':ENDTIME}, endtime=v_curtime)
        v_fid = fn_create_cirela(ci_type_djson[0]['SOURCE_FID'],ci_type_djson[0]['TARGET_FID'], ci_type_djson[0]['TYPE_FID'], 
                      ci_input.get('owner',ci_type_djson[0]['OWNER']), ci_type_djson[0]['FAMILY_ID'], ci_input.get('change_log',ci_type_djson[0]['CHANGE_LOG']))
       
        return v_fid
    

if __name__ == "__main__":  
    app = web.application(urls, globals())
    app.run()
