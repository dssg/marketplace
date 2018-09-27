import os
from csv import DictReader

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from dssgmkt.models.user import Skill


class Command(BaseCommand):

    help = 'Loads the initial skill data in the database'

    def handle(self, **options):
        path = os.path.join(settings.BASE_DIR, 'dssgmkt', 'data', 'skills.csv')
        self.stdout.write('Loading skills file {0}'.format(path))

        with open(path) as csvfile:
            reader = DictReader(csvfile, ['area', 'name'])
            for row in reader:
                try:
                    (new_skill, created) = Skill.objects.get_or_create(**row)
                    if created:
                        self.stdout.write('Created skill {}'.format(new_skill))
                    else:
                        self.stdout.write('Skill exists {}'.format(new_skill))
                except Exception as exc:
                    self.stdout.write(self.style.WARNING('Failed to create skill ({} {}) -- ({})'.format(row['name'], row['area'], exc)))

        self.stdout.write(self.style.SUCCESS('Finished loading skills.'))
