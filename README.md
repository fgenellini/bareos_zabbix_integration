bareos_zabbix_integration
=========================

Scripts and template to integrate bareos with zabbix.

Abilities
---------
* separate monitoring for each job
* low-level auto-discovery of new jobs
* send emails about jobs

Workflow
---------
For each job it's exit status and parameters are forwarded to Zabbix.

Triggers
--------
* Job exit status indicates error
* Job was not launched for 36 hours
* FD non-fatal errors occured
* SD errors occured
* Verify job failed
 
Installation
------------
 
* cd /etc/bareos
* git clone https://github.com/paleg/bareos_zabbix_integration.git
* Make sure that zabbix user can launch bconsole and get output of 'show jobs' command (add 'zabbix' user to 'bareos' group)
* Tweak conf.py:
	* path to zabbix agent conf
	* bconsole config file
	* timeout for bconsole command in seconds (default 5 seconds)
    * log dir
    * email settings ('From' header and smtp server)
* Add UserParameter from to zabbix_agentd.conf ( "UserParameter=bareos.jobs,/etc/bareos/bareos_zabbix_integration/get-bareos-jobs-json.py" )
* Config Messages resource in bareos-dir.conf. ( Samples can be found with "./notify.py --help" and "./notify_operator.py --help" )
* Add template MyTemplate_Bareos.xml to zabbix. Assign it to host with bareos-director.
* Disable auto-generated triggers for jobs that are not backup type(restore jobs, ...)
