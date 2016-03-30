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

urls = ( '/ciattr/(.*)', 'CIATTR',
         '/ciattr', 'ciattr',  )

db = web.database(dbn='oracle', user='cmdb', pw='cmdb123', db='cffexcmdb')
#Define time stamp 9999/12/31 23:59:59
ENDTIME = str(int('99991231235959'))
DELETETIME = str('00000000000000')

def fn_create_ciattr(i_value,i_description,i_type_fid,i_ci_fid,i_owner,i_family_id,i_change_log,i_endtime=ENDTIME):    
    #Function：create ci_attribute
    v_cad = 'PCAD00000001'
    v_fad = 'FCAD00000001'
    ci_id = db.query('select max(id) cad, max(family_id) fad from t_ci_attribute ')
    #Although there will be only one record, it also needs to iteratively generate the dict. It will raise an error if directly transforming ci_id[0] to json format
    ci_as_dict = []
    for ci in ci_id:
        ci_as_dict.append(ci)
    
    v_json = json.dumps(ci_as_dict).decode("GB2312")
    v_djson = json.loads(v_json,encoding="gb2312")
    v_num = len(v_djson)
    #Take the default value when inserting the first record
    if v_num <> 0 :
        v_cad = v_djson[0]['CAD']
        v_fad = v_djson[0]['FAD']
        v_cad = 'PCAD' + str(string.atoi(v_cad[4:])+1).rjust(8,'0')
        if i_family_id == None :
            v_fad = 'FCAD' + str(string.atoi(v_fad[4:])+1).rjust(8,'0')
        else:
            v_fad = i_family_id
    v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
    n = db.insert('t_ci_attribute',id = v_cad,value = i_value, description = i_description, type_fid = i_type_fid, ci_fid = i_ci_fid, 
                  owner = i_owner, starttime = v_curtime, endtime = i_endtime, family_id = v_fad, change_log = i_change_log)
    return v_fad

def fn_delete_ciattr(i_family_id,i_curtime,i_change_log):
    v_ct_fids = db.query("select distinct a.value, convert(a.description,'utf8') description, a.type_fid, a.ci_fid, a.owner, a.family_id from t_ci_attribute a where a.endtime = $endtime and a.family_id = $fid ",vars={'endtime':ENDTIME,'fid':i_family_id})
    ci_as_dict = []
    for ci in v_ct_fids:
        ci_as_dict.append(ci)
    ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
    ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
    #delete the record
    n = db.update('t_ci_attribute', where='family_id = $fid and endtime = $endtime', vars={'fid':i_family_id,'endtime':ENDTIME}, endtime=i_curtime)
    #insert a new record and set the endtime=deletetime
    v_fid = fn_create_ciattr(ci_type_djson[0]['VALUE'], ci_type_djson[0]['DESCRIPTION'], ci_type_djson[0]['TYPE_FID'], ci_type_djson[0]['CI_FID'],
                      ci_type_djson[0]['OWNER'], ci_type_djson[0]['FAMILY_ID'], i_change_log,DELETETIME)
    return n

class CIATTR:

   def GET(self,fid):
       ci_rec = db.query("select distinct d.name citype_name, b.name ci_name, c.name ciat_name, a.value, convert(a.description,'utf8') description, a.type_fid, a.ci_fid, a.owner, a.family_id, a.change_log from t_ci_attribute a, t_ci b, t_ci_attribute_type c, t_ci_type d where a.endtime = $endtime and b.endtime = $endtime and c.endtime = $endtime and d.endtime = $endtime and b.type_fid = d.family_id and c.ci_type_fid = d.family_id and a.family_id = $fid  and a.type_fid = c.family_id and a.ci_fid = b.family_id",vars={'endtime':ENDTIME,'fid':fid})
       ci_as_dict = []
       for ci in ci_rec:
           ci_as_dict.append(ci)
       ci_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
       return ci_json
   
class ciattr:

   def GET(self):
       all_col = ('value','description','type_fid','ci_fid','owner','family_id','time','change_log','citype_name','ci_name','ciat_name','value_type') 
       ci_input = web.input()
       condition = " "
       for col in range(len(all_col)):
           col_name = all_col[col]
           value = ci_input.get(col_name,None)
           if value <> None:
               if col_name == 'time' :
                   condition = condition + "a.starttime <= '" + value + "' and a.endtime > '" + value + "' and b.starttime <= '" + value + "' and b.endtime > '" + value + "' and c.starttime <= '" + value + "' and c.endtime > '" + value + "' and d.starttime <= '" + value + "' and d.endtime > '" + value + "' and "
               elif col_name == 'citype_name':
                   condition = condition + "d.name = '" + value + "' and "
               elif col_name == 'ci_name':
                   condition = condition + "b.name = '" + value + "' and "
               elif col_name == 'ciat_name':
                   condition = condition + "c.name = '" + value + "' and "
               elif col_name == 'value_type':
                   condition = condition + "c.value_type = '" + value + "' and "
               else :
                   condition = condition + "a." + col_name + " = '" + value + "' and "
           if value == None and col_name == 'time':
               condition = condition + "a.endtime = '" + ENDTIME + "' and b.endtime = '" + ENDTIME + "' and c.endtime = '" + ENDTIME + "' and d.endtime = '" + ENDTIME + "' and "
               
       v_sql = "select distinct d.name citype_name, b.name ci_name, c.name ciat_name, c.value_type, a.value, convert(a.description,'utf8') description, a.type_fid, a.ci_fid, a.owner, a.family_id, a.change_log from t_ci_attribute a, t_ci b, t_ci_attribute_type c, t_ci_type d where " + condition + "a.type_fid = c.family_id and a.ci_fid = b.family_id and b.type_fid = d.family_id and c.ci_type_fid = d.family_id "
       ci_recs = db.query(v_sql)
       ci_as_dict = []
       for ci in ci_recs:
           ci_as_dict.append(ci)
       ci_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
#        import sys,httplib, urllib 
#        params = urllib.urlencode({'fid':'FCAD00000002','change_log':'test'})
#        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
#        con2  =   httplib.HTTPConnection("localhost:8080") 
#        con2.request("DELETE","/ciattr",params,headers) 
#        con2.close()

       return ci_json
       
   def POST(self):
        ci_input = web.input()
        #Besides some fields in t_ci_attribute, input parameters also include the "name" field in t_ci and t_ci_attribute_type  
        v_ct_fids = db.query('select distinct a.family_id ci_fid,b.family_id type_fid from t_ci a, t_ci_attribute_type b where a.family_id=$cifid and a.endtime=$endtime and b.family_id=$ciattrtypefid and b.endtime=$endtime and a.type_fid=b.ci_type_fid',vars={'endtime':ENDTIME,'cifid':ci_input.get('ci_fid',None),'ciattrtypefid':ci_input.get('ci_attrtype_fid',None)})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there is no relative family id in table T_CI and T_CI_ATTRIBUTE_TYPE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one relative family ids in table T_CI and T_CI_ATTRIBUTE_TYPE
        v_ci_fid = json_de[0]['CI_FID']
        v_ciattp_fid = json_de[0]['TYPE_FID']
        
        #Users don't need to input the family_id . The afferent parameter for the function is null
        v_fid = fn_create_ciattr(ci_input.get('value',None), ci_input.get('description',None), v_ciattp_fid, v_ci_fid,
                      ci_input.get('owner',None), None, 'initialization')
        return v_fid

   def DELETE(self):
        input_data = web.data()
        data = urlparse.parse_qs(input_data)
        v_ct_fids = db.query("select distinct a.value from t_ci_attribute a where a.endtime = $endtime and a.family_id = $fid ",vars={'endtime':ENDTIME,'fid':data['fid'][0]})
        json_en = demjson.encode(v_ct_fids)
        json_de = demjson.decode(json_en)
        v_ct_fid_num = len(json_de)
        if v_ct_fid_num == 0:
            return 2 #there are no records to delete in table T_CI_ATTRIBUTE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to delete in table T_CI_ATTRIBUTE
       
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        #delete t_ci_attribute
        n = fn_delete_ciattr(data['fid'][0],v_curtime,data['change_log'][0])
        return n
    
   def PUT(self):
        ci_input = web.input()
        v_ct_fids = db.query("select distinct a.value, convert(a.description,'utf8') description, a.type_fid, a.ci_fid, a.owner, a.family_id, a.change_log from t_ci_attribute a where a.endtime = $endtime and a.family_id = $fid ",vars={'endtime':ENDTIME,'fid':ci_input.get('fid',None)})
        ci_as_dict = []
        for ci in v_ct_fids:
           ci_as_dict.append(ci)
        ci_type_json = json.dumps(ci_as_dict, indent = 4,ensure_ascii=False, separators = (',',':')).decode("GB2312")
        ci_type_djson = json.loads(ci_type_json,encoding="gb2312")
        v_ct_fid_num = len(ci_type_djson)

        if v_ct_fid_num == 0:
            return 2 #there are no records to modify in table T_CI_ATTRIBUTE
        elif v_ct_fid_num > 1:
            return 3 #there are more than one records to modify in table T_CI_ATTRIBUTE
        v_curtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        n = db.update('t_ci_attribute', where='family_id = $fid and endtime = $endtime', vars={'fid':ci_input.get('fid'),'endtime':ENDTIME}, endtime=v_curtime)
        v_fid = fn_create_ciattr(ci_input.get('value',ci_type_djson[0]['VALUE']), ci_input.get('description',ci_type_djson[0]['DESCRIPTION']), ci_type_djson[0]['TYPE_FID'], ci_type_djson[0]['CI_FID'],
                      ci_input.get('owner',ci_type_djson[0]['OWNER']), ci_type_djson[0]['FAMILY_ID'], ci_input.get('change_log',ci_type_djson[0]['CHANGE_LOG']))
        return v_fid
    

if __name__ == "__main__":  
    app = web.application(urls, globals())
    app.run()
