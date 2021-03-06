from django.db import models

from utils.gen_utils import dict_2_django_choice


LOGE_NO_URIS = 1
LOGE_WEB_SERV_RESP = 100
LOGE_IMG_CONV_WARN = 101
LOGE_IMG_SYNC_ERR = 200

LOG_ERR_CODES = {
    LOGE_NO_URIS : 'no uris',
    LOGE_WEB_SERV_RESP: 'webserver response warning',
    LOGE_IMG_CONV_WARN: 'image convert warning',
    LOGE_IMG_SYNC_ERR: 'error when syncing images',
    }

class ErrLog(models.Model):
    err_code = models.IntegerField(choices=dict_2_django_choice(LOG_ERR_CODES))
    msg = models.TextField()
    item_id = models.CharField(max_length=200)
    plugin_module = models.CharField(max_length=100)
    plugin_name = models.CharField(max_length=100)
    time_created = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        if self.err_code < 100:
            print '****Logged an error!!'
            print '*\terr_code: [%i] %s' % (self.err_code, LOG_ERR_CODES[self.err_code])
            print '*\tmsg:     ', self.msg
            print '*\titem_id: ', self.item_id
            print '*\tplugin:  ', self.plugin_name
        super(ErrLog, self).save(*args, **kwargs)