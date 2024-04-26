import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    '''Класс комманды Django для импорта данных в базу.

    Допускает импорт данных моделей Ingredient и Tag из
    файла формата csv.
    '''

    def __init__(self):
        self.models = {
            'ingredients.csv': Ingredient,
            'tags.csv': Tag,
        }

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        model = None

        for key, value in self.models.items():
            if key in options['csv_file']:
                model = value
                break

        if model is not None:
            with open(options['csv_file'], encoding='utf-8') as file:
                reader = csv.reader(file)
                data_list = list()
                for row in reader:
                    if model == Ingredient:
                        data_list.append({
                            'name': row[0],
                            'measurement_unit': row[1]})
                    elif model == Tag:
                        data_list.append({
                            'name': row[0],
                            'color': row[1],
                            'slug': row[2]})

            model.objects.bulk_create([
                model(**data) for data in data_list
            ], ignore_conflicts=True)
