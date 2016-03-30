#coding: utf-8

import web
import webci_type
import webci_attr_type
import webci_relation_type
import webci
import webci_attr
import webci_relation
import sys,httplib, urllib

reload(sys)
sys.setdefaultencoding('utf-8')
render = web.template.render('templates/',cache=False)

urls = ( '/citype/(.*)', 'webci_type.CITYPE',
         '/citype', 'webci_type.citype',  
         '/ciattrtype/(.*)', 'webci_attr_type.ATTRTYPE',
         '/ciattrtype', 'webci_attr_type.attrtype',
         '/cirelatype/(.*)', 'webci_relation_type.RELATYPE',
         '/cirelatype', 'webci_relation_type.relatype', 
         '/ci/(.*)', 'webci.CI',
         '/ci', 'webci.ci',
         '/ciattr/(.*)', 'webci_attr.CIATTR',
         '/ciattr', 'webci_attr.ciattr',
         '/cirela/(.*)', 'webci_relation.RELA',
         '/cirela', 'webci_relation.rela',
         '/', 'index',
         '/host/(.*)', 'host',
         )

class index():
    def GET(self):       
        return web.seeother('static/index.html')


if __name__ == "__main__":  
    app = web.application(urls, globals())
    app.run()
