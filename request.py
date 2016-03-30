# -*- coding:utf-8 -*-

import requests
import urllib2
import json

def post(url, data):
    result = requests.post(url, data)

def put(url, data):
    result = requests.put(url, data)

def delete(url, data):
    jdata = json.dumps(data)
    request = urllib2.Request(url, jdata)
    request.get_method = lambda:'DELETE'        # 设置HTTP的访问方式
    request = urllib2.urlopen(request)


if __name__ == '__main__':

    url = 'http://localhost:8080/v1/citype'
    url1 = 'http://localhost:8080/v1/attrtype'
    url2 = 'http://localhost:8080/v1/relatype'

    # data = {
    #     "description":"主机",
    #     "name":"OS",
    #     "starttime":"20160322203300",
    #     "owner":"主机岗",
    #     "endtime":"99991231235959",
    #     "log":"初始化",
    #     "displayname" : "操作系统",
    # }

    # data1 = {
    #     "citype_fid" : "FCIT00000006",
    #     "description":"主机名",
    #     "name":"HOSTNAME",
    #     "owner":"主机岗",
    #     "displayname" : "主机名",
    #     'mandatory' : 'Y',
    #     'log' : '初始化',
    # }

    data = {
        'fid':'FCIT00000006',
        'name':'test',
        'displayname':'testdis',
        'description':'just test',
        'owner':'业务岗',
        'log':'第一次修改',
    }

    data1= {
        'fid' : 'FCAT00000003',
        'name': '123',
        'displayname' : 'test123',
        'description': 'just test',
        'mandatory' : 'N',
        'owner':'业务岗',
        'log': '第一次修改',
    }

    data2 = {
        'fid':'FCRT00000001',
        'name': '主机与网卡',
        'relation': 'include',
        'owner': 'host',
        #'log': '初始化',
        'log': '第一次修改',
    }

    data3 = {
        '1' : None,
        '2' : None,
    }

    #delete(url, data2)
    #put(url, data1)
    #post(url2, data2)
    put(url, data)
    # for i in range(10):
    #     data1['name'] = 'HOSTNAME' + str(i)
    #     post(url1, data1)
