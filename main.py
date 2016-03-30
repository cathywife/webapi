# -*- coding: utf-8 -*-

import sys
import web
import json
from common.Logger import Logger

reload(sys)
sys.setdefaultencoding('utf-8')

urls = (
    '/v1/citype'         ,   'v1.citype.citype',
    '/v1/citype/(.*)'    ,   'v1.citype.citype',
    '/v1/attrtype'       ,   'v1.attrtype.attrtype',
    '/v1/attrtype/(.*)'  ,   'v1.attrtype.attrtype',
    '/v1/relatype'       ,   'v1.relatype.relatype',
    '/v1/relatype/(.*)'  ,   'v1.relatype.relatype',

    '/v1/ci'             ,   'v1.ci.ci',
    '/v1/ci/(.*)'        ,   'v1.ci.ci',
    '/v1/attr'           ,   'v1.attr.attr',
    '/v1/attr/(.*)'      ,   'v1.attr.attr',
    '/v1/rela'           ,   'v1.rela.rela',
    '/v1/rela/(.*)'      ,   'v1.rela.rela',
    '/'                  ,   'index',
)

class index:
    def GET(self):
        accessList = {
            'ci'    :   'http://<IP>/ci',
        }

        return json.dumps(accessList)

def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")

    # You can use template result like below, either is ok:
    #return web.notfound(render.notfound())
    #return web.notfound(str(render.notfound()))

def internalerror():
    return web.internalerror("Bad, bad server. No donut for you.")


if __name__ == '__main__':
    logger = Logger(logname='log.txt', logger="cmdbapi").getlog()

    app = web.application(urls, globals())

    app.notfound = notfound
    app.internalerror = internalerror

    app.run()