import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        with open(options['csv_file'], encoding='utf-8') as file:
            reader = csv.reader(file)
            data_list = list()
            for row in reader:
                data_list.append({'name': row[0], 'measurement_unit': row[1]})

        Ingredient.objects.bulk_create([
            Ingredient(
                name=data['name'],
                measurement_unit=data['measurement_unit'],
            ) for data in data_list
        ])
