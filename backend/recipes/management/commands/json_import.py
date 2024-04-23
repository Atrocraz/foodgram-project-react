import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        with open(options['json_file'], encoding='utf-8') as f:
            data_list = json.load(f)

        Ingredient.objects.bulk_create([
            Ingredient(
                name=data['name'],
                measurement_unit=data['measurement_unit'],
            ) for data in data_list
        ])
