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

 Initial release: 2010-02-05
 Version 1.1 2010-06-09
"""

from optparse import make_option

from django.core.management.base import BaseCommand

from apps.multi_lingo.submitter import SubmitContent


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--single-run', action='store_true', dest='single-run', default=False,
            help='Process queue once then terminate.'),
        make_option('--flush-all', action='store_true', dest='flush-all', default=False,
            help='Completely erase all data.'),
        make_option('--drop-all', action='store_true', dest='drop-all', default=False,
            help='Remove all tables from db.'),
        make_option('--clear-pids', action='store_true', dest='clear-pids', default=False,
            help='Clear all process monitoring data.'),
    )
    help = """
    Helo
    """
    args = ''#[--daemon]'

    def handle(self, *args, **options):
        submitter = SubmitContent()
        submitter.run()

