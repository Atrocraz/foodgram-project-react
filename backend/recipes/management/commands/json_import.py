import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    '''Класс комманды Django для импорта данных в базу.

    Допускает импорт данных моделей Ingredient и Tag из
    файла формата json.
    '''

    def __init__(self):
        self.models = {
            'ingredients.csv': Ingredient,
            'tags.csv': Tag,
        }

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        model = None

        for key, value in self.models.items():
            if key in options['json_file']:
                model = value
                break

        with open(options['json_file'], encoding='utf-8') as file:
            data_list = json.load(file)

        if model is not None:
            model.objects.bulk_create([
                model(**data) for data in data_list
            ], ignore_conflicts=True)
