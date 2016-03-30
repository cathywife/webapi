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

reload(sys)
sys.setdefaultencoding('utf-8')

render = web.template.render('templates/')

urls = ( '/ciattrtype/(.*)', 'ATTRTYPE',
         '/ciattrtype', 'attrtype',  )

db = web.database(dbn='oracle', user='cmdb', pw='cmdb123', db='cffexcmdb')
#Define time stamp 9999/12/31 23:59:59
ENDTIME = str(int('99991231235959'))
DELETETIME = str('00000000000000')

def fn_create_ci_attrtype(i_name,i_description,i_type_fid,i_mandatory,i_owner,i_family_id,i_change_log,i_displayname, i_value_type, i_endtime = ENDTIME):
    #Function：create ci attribute type
    v_cat = 'PCAT00000001'
    v_fat = 'FCAT00000001'
    ct_id = db.query('select max(id) cid, max(family_id) fid from t_ci_attribute_type ')
    #Although there will be only one record, it also needs to iteratively generate the dict. It will raise an error if directly transforming ci_id[0] to json format
    ci_as_dict = []
    for ci in ct_id:
        ci_as_dict.append(ci)
    
    v_json = json.dumps(ci_as_dict).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    #Take the default value when inserting the first record
    if v_num <> 0 :
        v_cat = v_djson[0]['CID']
        v_fat = v_djson[0]['FID']
        v_cat = 'PCAT' + str(string.atoi(v_cat[4:])+1).rjust(8,'0')
        if i_family_id == None :
            v_fat = 'FCAT' + str(string.atoi(v_fat[4:])+1).rjust(8,'0')
        else:
            v_fat = i_family_id
    v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
    n = db.insert('t_ci_attribute_type',id = v_cat,name = i_name, description = i_description, ci_type_fid = i_type_fid, mandatory= i_mandatory, 
                  owner = i_owner, starttime = v_curtime, endtime = i_endtime, family_id = v_fat, change_log = i_change_log,displayname = i_displayname, value_type = i_value_type)
    return v_fat

def fn_delete_ci_attrtype(i_family_id,i_curtime,i_change_log):
    #Function: Delete ci attribute type
    v_ca_fids = db.query('select distinct a.family_id from t_ci_attribute a where a.type_fid = $fid and a.endtime = $endtime',vars={'fid':i_family_id,'endtime':ENDTIME})
    json_en = demjson.encode(v_ca_fids)
    json_de = demjson.decode(json_en)
    v_ca_fid_num = len(json_de)
    if v_ca_fid_num <> 0:
        for v_ca_fid in json_de:
            n = webci_attr.fn_delete_ciattr(v_ca_fid['FAMILY_ID'], i_curtime, i_change_log)
    v_ct_fids = db.query("select a.name ,convert(a.description,'utf8') description,a.ci_type_fid,a.mandatory, a.owner,a.family_id,convert(a.displayname,'utf8') displayname, a.value_type from t_ci_attribute_type a where a.endtime = $aendtime and a.family_id = $fid ",vars={'aendtime':ENDTIME,'fid':i_family_id})
    ci_as_dict = []
    for ci in v_ct_fids:
        ci_as_dict.append(ci)
    ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
    ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
    #delete the record                    
    n = db.update('t_ci_attribute_type', where='family_id = $fid and endtime = $endtime', vars={'fid':i_family_id,'endtime':ENDTIME}, endtime=i_curtime)
    #insert a new record and set the endtime=deletetime
    v_fid = fn_create_ci_attrtype(ci_type_djson[0]['NAME'], ci_type_djson[0]['DESCRIPTION'],  ci_type_djson[0]['CI_TYPE_FID'],ci_type_djson[0]['MANDATORY'],ci_type_djson[0]['OWNER'],
                                  ci_type_djson[0]['FAMILY_ID'], i_change_log,ci_type_djson[0]['DISPLAYNAME'], ci_type_djson[0]['VALUE_TYPE'], DELETETIME)        
    return n

class ATTRTYPE:

   def GET(self,fid):
       ci_attrtype = db.query("select b.name citype_name, a.name ,convert(a.description,'utf8') description,a.ci_type_fid,a.mandatory, a.owner,a.family_id,convert(a.displayname,'utf8') displayname,a.value_type,a.change_log from t_ci_attribute_type a ,t_ci_type b where a.ci_type_fid = b.family_id and a.endtime = $endtime and b.endtime = $endtime and a.family_id = $fid ",vars={'endtime':ENDTIME,'fid':fid})
       ci_as_dict = []
       for ci in ci_attrtype:
           ci_as_dict.append(ci)
       ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       return ci_type_json
   
class attrtype:

   def GET(self):
       all_col = ('name','description','ci_type_fid','mandatory','owner','family_id','time','change_log','citype_name','value_type') 
       citype_input = web.input()
       condition = " "
       for col in range(len(all_col)):
           col_name = all_col[col]
           value = citype_input.get(col_name,None)
           if value <> None:
               if col_name == 'time' :
                   condition = condition + "cat.starttime <= '" + value + "' and cat.endtime > '" + value + "' and b.starttime <= '" + value + "' and b.endtime > '" + value + "' and "
               elif col_name == 'citype_name':
                   condition = condition + "b.name = '" + value + "' and "
               else :
                   condition = condition + "cat." + col_name + " = '" + value + "' and "
           if value == None and col_name == 'time':
               condition = condition + "cat.endtime = '" + ENDTIME + "' and b.endtime = '" + ENDTIME + "' and "
               
       
       v_sql = "select b.name citype_name, cat.name ,convert(cat.description,'utf8') description,cat.ci_type_fid, cat.mandatory, cat.owner,cat.family_id,convert(cat.displayname,'utf8') displayname, cat.value_type, cat.change_log from t_ci_attribute_type cat, t_ci_type b where " + condition + " cat.ci_type_fid = b.family_id "
       ci_type = db.query(v_sql)
       ci_as_dict = []
       for ci in ci_type:
           ci_as_dict.append(ci)
       ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       
#        import sys,httplib, urllib
#        params = urllib.urlencode({'fid':'FCAT00000027','change_log':'test'})
#        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
#        con2  =   httplib.HTTPConnection("localhost:8080") 
#        con2.request("DELETE","/ciattrtype",params,headers) 
#        con2.close()
       
       return ci_type_json
    
   def POST(self):
        citype_input = web.input()
        #Besides some fields in t_ci_attribute_type, input parameters also include the "name" field in t_ci_type
        v_ct_fids = db.query('SELECT distinct ct.family_id FROM t_ci_type ct WHERE ct.endtime = $endtime and ct.family_id = $ctfid',vars={'endtime':ENDTIME,'ctfid':citype_input.get('ci_type_fid',None)})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there is no relative family_id in table T_CI_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one relative family_ids in table T_CI_TYPE
        v_ct_fid = json_de[0]['FAMILY_ID']
                       
        #Users don't need to input the family_id . The afferent parameter for the function is null
        v_fid = fn_create_ci_attrtype(citype_input.get('name',None), citype_input.get('description',None), v_ct_fid,
                                      citype_input.get('mandatory',None),
                      citype_input.get('owner',None), None, 'initialization', citype_input.get('displayname',None),
                                      citype_input.get('value_type',None))
        
        return v_fid
    
   def DELETE(self):
        input_data = web.data()
        data = urlparse.parse_qs(input_data)        
        v_ct_fids = db.query("SELECT distinct c.name FROM t_ci_attribute_type c WHERE  c.family_id = $fid and c.endtime = $endtime",vars={'fid':data['fid'][0],'endtime':ENDTIME})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #There are no records to delete in table t_ci_attribute_type
        elif v_ct_fid_num > 1:
            return 3 #There are more than one records to delete in table t_ci_attribute_type
        
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        #When deleting t_ci_attribute_type, we should delete all the relative attribute
        n = fn_delete_ci_attrtype(data['fid'][0],v_curtime,data['change_log'][0])
        return n
    
   def PUT(self):
        citype_input = web.input()
        v_ct_fids = db.query("select a.name ,convert(a.description,'utf8') description,a.ci_type_fid,a.mandatory, a.owner,a.family_id,convert(a.displayname,'utf8') displayname,a.value_type, a.change_log from t_ci_attribute_type a where a.endtime = $aendtime and a.family_id = $fid ",vars={'aendtime':ENDTIME,'fid':citype_input.get('fid',None)})
        ci_as_dict = []
        for ci in v_ct_fids:
           ci_as_dict.append(ci)
        ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
        ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
        v_ct_fid_num = len(ci_type_djson)
        if v_ct_fid_num == 0:
            return 2 #There are no records to modify in table t_ci_attribute_type
        elif v_ct_fid_num > 1:
            return 3 #There are more than one records to modify in table t_ci_attribute_type
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = db.update('t_ci_attribute_type', where='family_id = $fid and endtime = $endtime', vars={'fid':citype_input.get('fid'),'endtime':ENDTIME}, endtime=v_curtime)
        v_fid = fn_create_ci_attrtype(citype_input.get('name',ci_type_djson[0]['NAME']), citype_input.get('description',ci_type_djson[0]['DESCRIPTION']), 
                                      ci_type_djson[0]['CI_TYPE_FID'],citype_input.get('mandatory',ci_type_djson[0]['MANDATORY']),citype_input.get('owner',ci_type_djson[0]['OWNER']),
                                  ci_type_djson[0]['FAMILY_ID'], citype_input.get('change_log',ci_type_djson[0]['CHANGE_LOG']),citype_input.get('displayname',ci_type_djson[0]['DISPLAYNAME']),citype_input.get('value_type',ci_type_djson[0]['VALUE_TYPE']))        
        return v_fid

if __name__ == "__main__":  
    app = web.application(urls, globals())
    app.run()
