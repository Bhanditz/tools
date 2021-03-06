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
from django.conf.urls import *
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

#from django.contrib import databrowse

def top_index(request):
    return render_to_response("top_index.html", {'request': request,})


def logout_view(request):
    logout(request)
    return redirect('top_index')


urlpatterns = patterns('',
    # Example:
    # (r'^sip_web/', include('sip_web.foo.urls')),
    url(r'^$', top_index, name='top_index'),

    (r'^uris/', include('apps.plug_uris.urls')),
    (r'^sipm/', include('apps.sipmanager.urls')),
    (r'^stats/', include('apps.statistics.urls')),
    (r'^optout/', include('apps.optout.urls')),
    

    #(r'^databrowse/(.*)', databrowse.site.root),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', logout_view, name='logout'),

)


