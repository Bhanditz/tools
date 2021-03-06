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



"""


from django.db import models, connection

from utils.gen_utils import dict_2_django_choice

from apps.dummy_ingester.models import Request





# MDRS_ = MdRecord state
MDRS_CREATED = 1
MDRS_IDLE = 2
MDRS_PROCESSING = 3
MDRS_PROBLEMATIC = 4
MDRS_BROKEN = 5
MDRS_VERIFIED = 6

MDRS_STATES = {
    MDRS_CREATED: 'created',
    MDRS_IDLE: 'idle',
    MDRS_PROCESSING: 'processing',
    MDRS_PROBLEMATIC: 'problematic',
    MDRS_BROKEN: 'broken',
    MDRS_VERIFIED: 'verified',
    }

class MdRecordManager(models.Manager):

    def get_or_create(self, content_hash, source_data):
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM %s WHERE content_hash='%s'" % (
            self.model._meta.db_table, content_hash))
        if cursor.rowcount:
            # this can so not fail - i just refuse to do errorhandling for this call
            item = self.model.objects.filter(content_hash=content_hash)[0]
            was_created = False
        else:
            item = self.model(content_hash=content_hash, source_data=source_data)
            try:
                item.save()
                was_created = True
            except:
                # triggered for some duplicates, shouldnt happen but this solves it...
                item = self.model.objects.filter(content_hash=content_hash)[0]
                was_created = False
        return item, was_created


class MdRecord(models.Model):
    content_hash = models.CharField(max_length=64, unique=True)

    # source data is the original record, treated in the following way:
    #   each line from the file is stripped of initial and trailing whitespace
    #   then concatenated with one \n char, no trailing \n
    source_data = models.TextField()
    status = models.IntegerField(choices=dict_2_django_choice(MDRS_STATES),
                                 default = MDRS_CREATED)
    time_created = models.DateTimeField(auto_now_add=True,editable=False)
    time_last_change = models.DateTimeField(auto_now_add=True,editable=False)

    pid = models.FloatField(default=0,db_index=True) # what process 'owns' this item
    uniqueness_hash = models.CharField(max_length=100)
    urls_extracted = models.BooleanField(db_index=True,default=False)
    Enrichment_done = models.BooleanField(default=False)

    objects = MdRecordManager()



class RequestMdRecord(models.Model):
    request = models.IntegerField(db_index=True)
    md_record = models.IntegerField(db_index=True)
    #i = models.IntegerField(default=0, blank=True)
