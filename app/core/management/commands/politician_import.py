from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Politician, Party
from django.db import transaction
from django.utils import translation
import json
import traceback

class Command(BaseCommand):
    help = 'Imports politicians from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', help='JSON file to import')

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with open(options['json_file']) as f:
                data = json.load(f)

                for row in data:
                    try:
                        translation.activate(row.get('language'))

                        politician = Politician(
                            first_name = row.get('first_name'),
                            last_name  = row.get('last_name'),
                            email      = row.get('email'),
                            party = Party.objects.get(shortname=row.get('party')),
                            user = User.objects.get(username=row.get('user')),
                        )

                        politician.save()
                    except Exception:
                        print('Skipping politician row:\n-----')
                        print(row)
                        print('------')
                        print(traceback.format_exc())

        except Exception as e:
            print(str(e))

# vim: set sw=4:ts=4:et:
