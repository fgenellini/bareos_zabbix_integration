#!/usr/bin/env python

import sys
import subprocess
import re
import os
import argparse
from argparse import RawTextHelpFormatter
import logging
import smtplib
from email.mime.text import MIMEText
from zbxsend import Metric, send_to_zabbix

# Settings
from conf import conf

def sendmail(jname, jtype, jlevel, jexit_code, jmsg, recipients):
    subject = "Bacula: {0} {1} of {2} {3}".format(jlevel, jtype, jname, jexit_code)
    logging.debug( "sending email ({0}) to '{1}'".format(subject, recipients) )

    msg = MIMEText(jmsg)
    msg['Subject'] = subject
    msg['From'] = conf['email_from']
    msg['To'] = ', '.join(recipients)

    s = smtplib.SMTP( conf['email_server'] )
    s.sendmail( conf['email_from'], recipients, msg.as_string() )
    s.quit()

logging.basicConfig(
    format=u'%(levelname)-8s [%(asctime)s] %(message)s',
    level=logging.DEBUG,
    filename=u'{0}/{1}.log'.format(conf['log_dir'], os.path.basename(__file__))
)
logging.info('sys.argv: ' + repr(sys.argv))

# Handle incorrect call
# zbxsend is broken in 3.x (https://github.com/alledm/zbxsend/commit/a485c97a4f0c2fa46fe3192da9979cbeade752b4)
if sys.version_info >= (3,):
    logging.warn("Need python version 2.x to run")
    quit(1)

parser = argparse.ArgumentParser(
            formatter_class=RawTextHelpFormatter,
            description=
"""Simple script to send Bacula reports to Zabbix.
Should be used in Bacula-dir config instead of mail command:
    mail = <admin@localhost> = all, !skipped
    mailcommand = "{0} '%n' '%t' '%l' '%e' [--recipients '%r'] [--email-on-fail] [--email-on-success]"
Hostnames in Zabbix and Bacula must correspond
""".format(os.path.realpath(__file__))
                                )

parser.add_argument('job_name', help='job name (%%n)')
parser.add_argument('job_type', help='job type (%%t)')
parser.add_argument('job_level', help='job level (%%l)')
parser.add_argument('job_exit_code', help='job exit code (%%e)')

parser.add_argument('--recipients',
                    action='store',
                    type=lambda x: x.split(),
                    default=[],
                    help='space-separated list of report recipients (%%r)')
parser.add_argument('--email-on-fail',
                    action='store_true',
                    help='Send email about failed jobs to recipients')
parser.add_argument('--email-on-success',
                    action='store_true',
                    help='Send email about successed jobs to recipients')

args = parser.parse_args()

# Define how to get values from input
tests = (

    ("\s*FD Files Written:\s+([0-9]+)\s*",
        "bacula.fd_fileswritten",
        lambda x: x.group(1)),

    ("\s*SD Files Written:\s+([0-9]+)\s*",
        "bacula.sd_fileswritten",
        lambda x: x.group(1)),

    ("\s*FD Bytes Written:\s+([0-9][,0-9]*)\s+\(.*\)\s*",
        "bacula.fd_byteswritten",
        lambda x: x.group(1).translate(None, ",")),

    ("\s*SD Bytes Written:\s+([0-9][,0-9]*)\.*",
        "bacula.sd_byteswritten",
        lambda x: x.group(1).translate(None, ",")),

    ("\s*Last Volume Bytes:\s+([0-9][,0-9]*).*",
        "bacula.lastvolumebytes",
        lambda x: x.group(1).translate(None, ",")),

    ("\s*Files Examined:\s+([0-9][,0-9]*)\s*",
        "bacula.verify_filesexamined",
        lambda x: x.group(1).translate(None, ",")),

    ("\s*Non-fatal FD errors:\s+([0-9]+)\s*",
        "bacula.fd_errors_non_fatal",
        lambda x: x.group(1)),

    ("\s*SD Errors:\s+([0-9]+)\s*",
        "bacula.sd_errors",
        lambda x: x.group(1))

)

result = {}
result['bacula.job_exit_code'] = args.job_exit_code

in_msg = ""
# Get values from input
for line in sys.stdin.readlines():
    in_msg += line
    for regexp, key, value in tests:
        match = re.match(regexp, line)
        if match:
            # DEBUG
            logging.debug(line)
            result[key] = value(match)
            continue

logging.debug(repr(in_msg))
# DEBUG
logging.debug(repr(result))

metrics = []
for key, value in result.items():
    metrics.append( Metric(conf['hostname'], '{0}[{1}]'.format(key, args.job_name), value) )

# Send result to zabbix
logging.info( "sending metrics to '{0}': '{1}'".format(conf['zabbix_server'], metrics) )
send_to_zabbix(metrics, conf['zabbix_server'], 10051, 20)

# Send emails (if requested)
if (args.recipients and
    ((args.job_exit_code == 'OK' and args.email_on_success) or
     (args.job_exit_code != 'OK' and args.email_on_fail))):
    sendmail(args.job_name, args.job_type, args.job_level, args.job_exit_code, in_msg, args.recipients)
