"""
 Copyright 2010 EDL FOUNDATION

 Licensed under the EUPL, Version 1.1 or as soon they
 will be approved by the European Commission - subsequent
 versions of the EUPL (the "Licence");
 you may not use this work except in compliance with the
 Licence.
 You may obtain a copy of the Licence at:

 http://ec.europa.eu/idabc/eupl

 Unless required by applicable law or agreed to in
 writing, software distributed under the Licence is
 distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 express or implied.
 See the Licence for the specific language governing
 permissions and limitations under the Licence.


 Created by: Jacob Lundqvist (Jacob.Lundqvist@gmail.com)

 Maintains and runs tasks
"""

import os
import sys
import time
import threading

from django.core import exceptions
from django.conf import settings
from django.db import connection
from django.core.mail import send_mail

from utils.gen_utils import db_is_mysql, count_records

from apps.dummy_ingester.tasks import RequestParseNew

from apps.plug_uris import models as uri_models
from apps.plug_uris import tasks as uri_tasks
#from apps.base_item import models as item_models


from apps.base_item import mongo_exp as mongo_base
from apps.plug_uris import mongo_exp as mongo_uri
from apps.plug_uris.update_req_stats import UpdateRequestStats
from apps.dummy_ingester.reqlist import ReqListUpdater, ReqListNewModel


import sip_task
import models
import sync_imgs


# Since looking up in settings takes some extra cpu, important settings
# are cached within the module
PROCESS_SLEEP_TIME = settings.PROCESS_SLEEP_TIME
PLUGIN_FILTER = settings.PLUGIN_FILTER
SIPMANAGER_DBG_LVL = settings.SIPMANAGER_DBG_LVL


TASK_THROTTLE_TIME = 330

DB_RESET_INTERVAL = settings.DB_RESET_INTERVAL


class MainProcessor(sip_task.SipTask):
    ALL_TABLES = [("base_item_mdrecord", True),
                  ("base_item_requestmdrecord", False),

                  #('dummy_ingester_reqlist', False),
                  ("dummy_ingester_request", True),

                  #("ingqueue_ingqueue", False),
                  #("ingqueue_submitter", False),

                  ("log_errlog", False),

                  ("plug_uris_requri", False),
                  ("plug_uris_uri", True),
                  ("plug_uris_reqstats",False),
                  ("plug_uris_urisource", True),
                  ("sipmanager_processmonitoring", False)]



    SINGLE_INSTANCE_REC_FIELDS = ('europeana:object','europeana:isShownBy',
                                  'europeana:isShownAt')
    THREAD_MODE = sip_task.SIPT_NOT
    PRIORITY = sip_task.SIP_PRIO_NORMAL
    SHORT_DESCRIPTION = 'Main processor'


    def __init__(self, options, *args):
        super(MainProcessor, self).__init__(debug_lvl=SIPMANAGER_DBG_LVL)

        if 0:
            self.purge_duplicate_requests()
            sys.exit(0)
        if not settings.PRINT_LOG:
            print 'No progress will be printed, check logfile instead: %s' % settings.SIP_LOG_FILE

        if options['flush-all']:
            self.cmd_flush_all(*args)
            sys.exit(0)
        elif options['drop-all']:
            self.cmd_drop_all(*args)
            sys.exit(0)
        elif options['clear-pids']:
            self.cmd_clear_pids()
            sys.exit(0)
        elif options['find-dupes']:
            self.cmd_find_dupes(args[0])
            sys.exit(0)
        elif options['clear-bad-links']:
            self.cmd_clear_bad_links()
            sys.exit(0)
        elif options['clear-aborted-links']:
            self.cmd_clear_aborted_links()
            sys.exit(0)

        elif options['no-upsizing']:
            self.cmd_noupsizing()
            sys.exit(0)
        elif options['without-size']:
            self.cmd_without_size()
            sys.exit(0)
        elif options['mongify']:
            self.cmd_mongify()
            sys.exit(0)
        elif options['newrequest-model']:
            self.cmd_new_request_model()
            sys.exit(0)
        elif options['sync-imgs']:
            self.cmd_sync_imgs()
            sys.exit(0)
        elif options['update-reqlist']:
            self.cmd_update_requests()
            sys.exit(0)
        elif options['update-reqstats']:
            self.cmd_update_req_stats()
            sys.exit(0)
        self.single_run = options['single-run']
        self.tasks_init = [] # tasks that should be run first
        self.tasks = [] # list of all tasks found
        self.find_tasks()

    def run(self):
        "wrapper to catch Ctrl-C."
        self.register_app()
        keyboard_termination = False
        try:
            self.run2()
        except KeyboardInterrupt:
            keyboard_termination = True

        print
        print 'Terminating - will take a while to do a clean shutdown...'
        self.log('>>>>>   Shutdown requested')
        sip_task.PLUGINS_MAY_NOT_RUN = True
        t = time.time()
        time.sleep(1)
        
        # kill off all ongoing sync processes
        retcode, stdout, stderr = self.cmd_execute_output('killall rsync')
        retcode, stdout, stderr = self.cmd_execute_output('killall scp')
        # we dont really care bout errors above...
        
        while threading.active_count() > 1:
            if t + 60 < time.time():
                print '***** Killing remaining (%i) plugins agresivly' % (threading.active_count() -1)
                print '\t',
                for s in sip_task.RUNNING_PLUGINS:
                    print s,
                print
                sip_task.IS_TERMINATING = True
                break
            print '\tWaiting for %i plugins to terminate' % (threading.active_count() -1)
            time.sleep(5)
        self.log('=====   Shutding down, terminating operations   =====')
        if not sip_task.IS_TERMINATING:
            print 'Clean shutdown - database should be ok'
        else:
            print '*****  Enforced shutdown, please run: sipmanager --clear-pids  *****'
        if not keyboard_termination:
            for eadr in settings.ADMIN_EMAILS:
                send_mail('Thumbler bad termination', 'thumbler terminated without user request - probably a crach', '', 
                          [eadr], fail_silently=False)
            
        self.de_register_app()
        return

    def run2(self):
        """
        Main loop inside a Ctrl-C check
        """
        # First run all init tasks once
        self.log(' =====   Running init plugins   =====')
        for taskClass in self.tasks_init:
            tc = taskClass(debug_lvl=SIPMANAGER_DBG_LVL)
            self.log('\t%s' % tc.short_name())
            tc.run()

        self.log(' =====   Commencing operations   =====')
        self.log('Tastk start limits  = (%0.1f, %0.1f, %0.1f)' % settings.MAX_LOAD_NEW_TASKS)
        self.log('Task kill limits    = (%0.1f, %0.1f, %0.1f)' % settings.MAX_LOAD_RUNNING_TASKS)
        idle_count = 0
        t_reset_time = time.time()
        while sip_task.IS_TERMINATING == False:
            self.log('>>>>> mainloop starting <<<<<', 9)
            new_task_started = False
            busy = False
            if not sip_task.PLUGINS_MAY_NOT_RUN:
                for taskClass in self.tasks:
                    busy, loads = self.system_is_occupied()
                    if busy and taskClass.PRIORITY != sip_task.SIP_PRIO_HIGH:
                        self.log('  load too high, wont start new task', 9)
                        break # make sure we look att the taskClass prio and not our own...
                    task = taskClass(debug_lvl=SIPMANAGER_DBG_LVL)
                    if task.run():
                        new_task_started = True
                        # it was started
                        # should we allow one or more plugs / sleep period?
                        # if no set busy = True here
                        if self.task_throttling():
                            # If we recently terminated a task, do slow starting,
                            # just one task per timeslot
                            busy = True
                            break

            if self.single_run:
                self.log('Single run, aborting after one run-through')
                break # only run once


            if new_task_started:
                idle_count = 0
            else:
                idle_count += 1


            if DB_RESET_INTERVAL and (t_reset_time + DB_RESET_INTERVAL < time.time()) and (sip_task.PLUGINS_MAY_NOT_RUN == False):
                # only do this if nothing else is using PLUGINS_MAY_NOT_RUN
                if threading.active_count() > 1:
                    sip_task.PLUGINS_MAY_NOT_RUN = True
                    self.log('DB MAINT - terminating all plugins to reset db connections')
                    self.log('*** thread count %i' % threading.active_count())
                    time.sleep(5)
                    while threading.active_count() > 1:
                        self.log('DB-MAINT waiting for plugins to stop')
                        self.log('*** thread count %i' % threading.active_count())
                        time.sleep(5)
                    self.log('DB-MAINT resuming operations')
                    self.log('*** thread count %i' % threading.active_count())
                    sip_task.PLUGINS_MAY_NOT_RUN = False
                t_reset_time = time.time()

            if idle_count > 10:
                #self.cmd_clear_pids()
                idle_count = 0
                if SIPMANAGER_DBG_LVL > 7: # dont indicate idling too often...
                    if not models.ProcessMonitoring.objects.all().count():
                        self.log(' nothing to do for the moment...')

            if self.task_throttling():
                t = max(PROCESS_SLEEP_TIME, 60)
                self.log('>>> throtled waiting', 5)
            else:
                t = PROCESS_SLEEP_TIME
            self.log('>>>>> mainloop going to sleep <<<<<', 9)
            time.sleep(t)

        self.log('>>>>> mainloop has been asked to terminate <<<<<', 1)
        return True



    def register_app(self):
        pidfile = self.check_for_pidfile()
        pid = os.getpid()
        open(pidfile,'w').write('%i\n' % pid)

    def de_register_app(self):
        pidfile = self.register_pidfile()
        os.remove(pidfile)

    def check_for_pidfile(self):
        pidfile = self.register_pidfile()
        if os.path.exists(pidfile):
            print '*** sipmanager already running, pidfile:', pidfile
            sys.exit(1)
        return pidfile

    def register_pidfile(self):
        pidfile = os.path.join(os.path.split(settings.SIP_LOG_FILE)[0],'sipmanager.pid')
        return pidfile

    def task_throttling(self):
        "Indicate a reasent task kill."
        if (sip_task.LAST_TASK_TERMINATION + TASK_THROTTLE_TIME) > time.time():
            b = True
        else:
            b = False
        return b


    """
    Scan all apps, find the tasks module and add all classes found there

    """
    def find_tasks(self):
        self.log(' =====   Scanning for plugins   =====')
        tasks = []
        for app in settings.INSTALLED_APPS:
            if not app.find('apps') == 0:
                continue
            try:
                exec('from %s.tasks import task_list' % app )
            except ImportError, e:
                if e.args[0].find('No module named ') != 0:
                    raise ImportError, e
                continue
            plugin_content = ['Plugins found %s:' % app]
            for task in task_list:
                if PLUGIN_FILTER and not task.__name__ in PLUGIN_FILTER:
                    # we dont ever want to prevent task inits to run...
                    continue
                plugin_content.append(task.__name__)
                if task.INIT_PLUGIN:
                    self.tasks_init.append(task)
                    continue
                resource_hog = False
                if task.PLUGIN_TAXES_CPU:
                    resource_hog = True
                if task.PLUGIN_TAXES_DISK_IO:
                    resource_hog = True
                if task.PLUGIN_TAXES_NET_IO:
                    resource_hog = True
                tasks.append((task.PRIORITY, task))
            self.log(' '.join(plugin_content), 1)

        tasks.sort()
        for pri, task in tasks:
            self.tasks.append(task)


    def cmd_find_dupes(self, fname):
        rpn = RequestParseNew(debug_lvl=5)
        rpn.pm = models.ProcessMonitoring(pid=rpn.pid,
                                          plugin_module = self.__class__.__module__,
                                          plugin_name = self.__class__.__name__,
                                          )
        rpn.pm.save()

        rec_count = count_records(fname)
        print 'Scanning for dup-keys in', fname
        print '\t(%i records)' % rec_count
        rpn.task_starting('dup field finder', rec_count, display=False)
        rec_count = rpn.find_records(fname, self.scan_rec_for_dupes)


    def scan_rec_for_dupes(self, record):
        rec_dct = {}
        dup_key_found = False
        for field in record:
            key = field.split('>')[0][1:]
            value = field.replace(key,'').replace('<>','').replace('</>','')
            if key in self.SINGLE_INSTANCE_REC_FIELDS:
                if key not in rec_dct.keys():
                    rec_dct[key] = []
                else:
                    dup_key_found = True
                rec_dct[key].append(value)
            else:
                rec_dct[key] = value

        if dup_key_found:
            print rec_dct['europeana:uri']
            for key in self.SINGLE_INSTANCE_REC_FIELDS:
                if key in rec_dct.keys() and len(rec_dct[key]) > 1:
                    for v in rec_dct[key]:
                        print '\t', key, v


    def cmd_flush_all(self, *args):
        if db_is_mysql:
            sql = 'TRUNCATE %s'
        else:
            sql = 'TRUNCATE %s CASCADE;commit'

        self.do_sql_admin(self.ALL_TABLES, sql, 'flush')
        return True

    def cmd_drop_all(self, *args):
        if db_is_mysql:
            sql = 'DROP TABLE %s'
        else:
            sql = 'DROP TABLE %s CASCADE;commit'
        self.do_sql_admin(self.ALL_TABLES, sql, 'remove')
        if 'force' in args:
            self.do_sql_admin( (('dummy_ingester_reqlist', False),), sql, 'remove')
        return True

    def cmd_clear_pids(self):
        self.check_for_pidfile()
        cursor = connection.cursor()
        self.log('clear-pids running!')
        cursor.execute('begin')
        cursor.execute("TRUNCATE %s_processmonitoring" % __name__.split('.')[-2])

        # Clear request in progress
        cursor.execute('UPDATE dummy_ingester_request SET status=0 WHERE status=1')

        for table, has_pid in self.ALL_TABLES:
            if has_pid:
                cursor.execute('UPDATE %s SET pid=0 WHERE pid > 0' % table)
                
        cursor.execute('commit')
        self.log('clear-pids done!')

    def cmd_clear_bad_links(self):
        cursor = connection.cursor()
        sql = ["UPDATE %s" % uri_models.TBL_URIS]
        sql.append("SET status=%i" % uri_models.URIS_CREATED)
        sql.append(",mime_type='', file_type='', pid=0, url_hash=''")
        sql.append(",content_hash='', err_code=%i, err_msg=''" % uri_models.URIE_NO_ERROR)
        sql.append("WHERE status != %i" % uri_models.URIS_COMPLETED)
        self.log('Clearing bad links from %s' % uri_models.TBL_URIS)
        cursor.execute(" ".join(sql))
        self.log('Clearing bad links from %s - found %i items' % (uri_models.TBL_URIS, cursor.rowcount))
        cursor.execute("commit")


    def cmd_clear_aborted_links(self):
        self.log('clear-half-links starting...')
        cursor = connection.cursor()
        sql = ["UPDATE %s" % uri_models.TBL_URIS]
        sql.append("SET status=%i" % uri_models.URIS_CREATED)
        sql.append(", err_code=%i, err_msg=''" % uri_models.URIE_NO_ERROR)
        sql.append("WHERE status != %i" % uri_models.URIS_COMPLETED)
        sql.append("AND status != %i" % uri_models.URIS_FAILED)
        self.log('Clearing half processed links from %s' % uri_models.TBL_URIS)
        cursor.execute(" ".join(sql))
        self.log('Clearing half processed links from %s - found %i items' % (uri_models.TBL_URIS, cursor.rowcount))
        cursor.execute("commit")
        


    def cmd_noupsizing(self):
        """
        regenerate any upsized image to a non upsized state
        """
        self.log('noupsizing starting...')
        self.reziseCommon("AND (org_w<%i OR org_h<%i)" % uri_tasks.FULLDOC_SIZE)
        self.log('noupsizing done!')


    def cmd_without_size(self):
        self.log('without_size starting...')
        self.reziseCommon("AND org_w=0")
        self.log('without_size done!')

    def cmd_mongify(self):
        self.log('Mongify starting...')
        import pymongo
        from pymongo import Connection
        connection = Connection()
        db = connection.ingestion_manager
        self.post_prepare()

        #mongo_base.dataset(self, db.dataset)
        mongo_base.mdr(self, db.mdr)
        mongo_uri.uri(self, db.uri)

        self.log('Mongify done...')


    def cmd_update_requests(self):
        self.log('Update requests starting...')
        rl = ReqListUpdater(self.log)
        rl.run()
        self.log('Update requests done...')

    def cmd_new_request_model(self):
        self.log('New request model starting...')
        rnm = ReqListNewModel()
        rnm.run()
        self.log('New request model done...')

    def cmd_sync_imgs(self):
        self.log('Sync images starting...')
        if not settings.SYNC_SOURCE:
            raise exceptions.ImproperlyConfigured('Missing setting SYNC_SOURCE')
        if not settings.SYNC_DEST:
            raise exceptions.ImproperlyConfigured('Missing setting SYNC_DEST')
        if not settings.IMG_SYNC_TOUCHFILE:
            raise exceptions.ImproperlyConfigured('Missing setting IMG_SYNC_TOUCHFILE')
        img_syncer = sync_imgs.ImgSyncer(settings.SIPMANAGER_DBG_LVL)   
        #img_syncer.run(settings.SYNC_SOURCE, settings.SYNC_DEST)
        self.log('Sync images done...')

    def cmd_update_req_stats(self):
        self.log('Updating request statistics starting...')
        settings.STATS_UPDATE_INTERVALL = 1 # ensure it is run
        rnm = UpdateRequestStats()
        rnm.run(now=True)
        self.log('Updating request statistics done...')

    def reziseCommon(self, extra_where):
        urisources = uri_models.Uri.objects.filter(pid=0).values('pk')
        self.cursor = connection.cursor()
        sql = ["SELECT id, mime_type,url_hash, content_hash, org_w, org_h"]
        sql.append("FROM %s" % uri_models.TBL_URIS)
        sql.append("WHERE status=%i AND err_code=0" % uri_models.URIS_COMPLETED)
        sql.append("AND item_type=%i" % uri_models.URIT_OBJECT)
        sql.append(extra_where)
        sql.append("ORDER BY id")
        self.log('finding small imgs in %s' % uri_models.TBL_URIS)
        self.cursor.execute(" ".join(sql))
        self.validate_save = uri_tasks.UriValidateSave()
        items = self.cursor.fetchall()
        all_items = len(items)
        count = i = 0
        self.initial_message = 'regenerating small imgs without upsizing'
        self.SHORT_DESCRIPTION = 'unResizeSmall'
        self.post_prepare()
        self.task_starting('', steps=all_items)
        count_full = count_brief = 0
        for url_id, mime_type,url_hash, content_hash, org_w, org_h in items:
            count += 1
            self.task_time_to_show(count)
            lvl_1 = content_hash[:2]
            lvl_2 = content_hash[2:4]
            org_fname = '%s/original/%s/%s/%s' % (settings.SIP_OBJ_FILES, lvl_1, lvl_2, content_hash)

            if org_w == 0 or org_h == 0:
                try:
                    org_w, org_h = self.get_img_size(url_id, org_fname, content_hash)
                except:
                    print '*** no size found for [%i] %s' % (url_id, content_hash)
                    continue
            # if too small, regenerate thumbs with white frame
            #if i > 500:
            #    self.cursor.execute('commit')
            #    i = 0
            try:
                if (org_w < uri_tasks.FULLDOC_SIZE[0]) or (org_h < uri_tasks.FULLDOC_SIZE[1]):
                    count_full += 1
                    if not self.small_fulldoc(url_id, org_fname, url_hash, org_w, org_h):
                        print '*** Failed fulldoc [%i] %s' % (url_id, content_hash)
                        self._inactivate_bad_uri(url_id, 'failed to resize fulldoc')
                        continue
                if (org_w < uri_tasks.BRIEFDOC_SIZE[0]) or (org_h < uri_tasks.BRIEFDOC_SIZE[1]):
                    count_brief += 1
                    if not self.small_briefdoc(url_id, org_fname, url_hash, org_w, org_h):
                        print '*** Failed briefdoc [%i] %s' % (url_id, content_hash)
                        self._inactivate_bad_uri(url_id, 'failed to resize briefdoc')
                        continue
            except:
                print '*** Failed rezise [%i] %s' % (url_id, content_hash)
                self._inactivate_bad_uri(url_id)
        print 'fixed brief: %i  fixed full: %i' % (count_brief, count_full)


    def _inactivate_bad_uri(self, uid, msg='detected error during resizeCommon'):
        print '*** _inactivate_bad_uri not requri safe...'
        sys.exit(1)
        cursor2 = connection.cursor()
        sql = ["UPDATE %s" % uri_models.TBL_URIS]
        sql.append("SET status=%i, err_code=%i," % (uri_models.URIS_FAILED, uri_models.URIE_OTHER_ERROR))
        sql.append("err_msg='%s'" % msg)
        sql.append("WHERE id=%i" % uid)
        cursor2.execute(" ".join(sql))

        sql = ["UPDATE %s" % uri_models.TBL_REQURI]
        sql.append("SET status=%i, err_code=%i" % (uri_models.URIS_FAILED, uri_models.URIE_OTHER_ERROR))
        sql.append("WHERE uri_id=%i" % uid)
        cursor2.execute(" ".join(sql))

    def get_img_size(self, url_id, org_fname, content_hash):
        cmd = 'identify %s[0]' % org_fname
        retcode, stdout, stderr = self.cmd_execute_output(cmd)
        if retcode or stdout:
            sip_task.SipTaskException('Failed to find img size for [%s] %s' % (url_id, content_hash))
        size = stdout.split(org_fname)[-1].split()[1].split('x')
        try:
            org_w = int(size[0])
            org_h = int(size[1])
        except:
            sip_task.SipTaskException('Failed to extract img size for [%s] %s - [%s]' % (url_id, content_hash, size))
        sql = ["UPDATE %s" % uri_models.TBL_URIS]
        sql.append("SET org_w=%i, org_h=%i" % (org_w, org_h))
        sql.append("WHERE id=%i" % url_id)
        self.cursor.execute(" ".join(sql))
        return org_w, org_h

    def small_fulldoc(self, url_id, org_fname, url_hash, org_w, org_h):
        thumb_fname = self._img_size_fname(url_hash)
        return self.validate_save.generate_fulldoc(thumb_fname, org_fname, org_w, org_h)

    def small_briefdoc(self, url_id, org_fname, url_hash, org_w, org_h):
        thumb_fname = self._img_size_fname(url_hash)
        return self.validate_save.generate_briefdoc(thumb_fname, org_fname, org_w, org_h)

    def _img_size_fname(self, url_hash):
        thumb_fname = self.validate_save.file_name_from_hash(url_hash)
        return thumb_fname


    #def cmd_generate_img_sizes(self):



    def do_sql_admin(self,lst, sql, action='manipulated'):
        cursor = connection.cursor()
        for table, has_pid in lst:
            try:
                cursor.execute(sql % table)
                print action, table
            except:
                print 'Failed to %s %s' % (action, table)

    def purge_duplicate_requests(self):
        for req in (#404,405,406,407,408,409,410,411,
                    #412,413,422,423,424,425,
                    426,427,428,429,430,431,432,433,434,435,
                    436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,460,):
            self.purge_one_duplicate_request(req)

    def purge_one_duplicate_request(self, req):
        print '*** purge_one_duplicate_request not requri safe...'
        sys.exit(1)
        
        print 'removing duplicates for request', req
        cursor = connection.cursor()

        print '\tclearing plug_uris_requri ',
        sys.stdout.flush()
        sql = "delete from plug_uris_requri where req=%i" % req
        cursor.execute(sql)
        print cursor.rowcount

        print '\tclaring base_item_mdrecord ',
        sys.stdout.flush()
        sql = ["delete from base_item_mdrecord where id in ( select m.id"]
        sql.append("from base_item_requestmdrecord r, base_item_mdrecord m")
        sql.append("where r.request=%i and m.id=r.md_record)" % req)
        cursor.execute(" ".join(sql))
        print cursor.rowcount

        print '\tclaring base_item_requestmdrecord ',
        sys.stdout.flush()
        sql = "delete from base_item_requestmdrecord where request=%i" % req
        cursor.execute(sql)
        print cursor.rowcount

        print '\tclaring dummy_ingester_request ',
        sys.stdout.flush()
        sql = "delete from dummy_ingester_request where id=%i" % req
        cursor.execute(sql)
        print cursor.rowcount

        print '\tcommiting change ',
        sys.stdout.flush()
        cursor.execute("commit")
        print 'done!'




"""
  Request actions

  all items with status REQS_INIT should be parsed and MdRecords created
"""
