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

from django.conf.urls import patterns, include, url

import views


urlpatterns = patterns('',

    url(r'^restart_dashboard/', views.restart_dashboard, name='restart_dashboard'),
    url(r'^monitor/$', views.show_monitor, name='sipm_monitor'),
    url(r'^monitor/oldest_update/$', views.oldest_update, name='sipm_monitor_oldest'),
)
