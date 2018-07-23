from django.core.management.base import BaseCommand, CommandError
from dssgmkt.models.user import Skill
from csv import DictReader
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Loads the initial skill data in the database'

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR,'dssgmkt','data','skills.csv')
        self.stdout.write('Loading skills file {0}'.format(path))
        with open(path) as csvfile:
            reader = DictReader(csvfile, ['area', 'name'])
            for row in reader:
                new_skill = Skill()
                new_skill.area = row['area']
                new_skill.name = row['name']
                try:
                    new_skill.save()
                    self.stdout.write('Created skill {0}'.format(new_skill))
                except:
                    self.stdout.write(self.style.WARNING('Failed to create skill {0}'.format(new_skill)))
        self.stdout.write(self.style.SUCCESS('Finished loading skills.'))
