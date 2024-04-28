import csv
from os.path import isfile

from django.conf import settings
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
        parser.add_argument('csv_file', type=str, nargs='?',
                            default=settings.DEFAULT_IMPORT_LOCATIONS)

    def handle(self, *args, **options):
        if options['csv_file'] == settings.DEFAULT_IMPORT_LOCATIONS:
            file_list = options['csv_file'].split(',')

            for file in file_list:
                self.add_to_database(file + '.csv')
        else:
            self.add_to_database(options['csv_file'])

    def add_to_database(self, file_path):
        if not isfile(file_path):
            print(f'Файл {file_path} не найден.')
            return

        model = None

        for key, value in self.models.items():
            if key in file_path:
                model = value
                break

        if model is not None:
            with open(file_path, encoding='utf-8') as file:
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
            if model == Ingredient:
                print('Объекты добавлены в базу данных для модели Ингредиент.')
            elif model == Tag:
                print('Объекты добавлены в базу данных для модели Тег.')
