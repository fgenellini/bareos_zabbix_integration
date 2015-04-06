from socket import gethostname
from ConfigParser import ConfigParser
from StringIO import StringIO

conf = {
            'log_dir': "/var/log/bareos/",
            'zabbix_agent_conf': "/etc/zabbix/zabbix_agentd.conf",
            'bconsole_conf_file': "/etc/bareos/bconsole.conf",
            'bconsole_wait': 5,
            'email_from': "Bareos <bareos@localhost>",
            'email_server': "127.0.0.1"
       }

zcfg = ConfigParser()
with open(conf['zabbix_agent_conf']) as stream:
    fakefile = StringIO("[global]\n" + stream.read())
    zcfg.readfp(fakefile)
zserver = zcfg.get('global', 'server').split(',')[0]

conf['hostname'] = gethostname()
conf['zabbix_server'] = zserver
