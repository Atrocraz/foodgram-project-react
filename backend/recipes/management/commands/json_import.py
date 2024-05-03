import json
from os.path import isfile

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Класс комманды Django для импорта данных в базу.

    Допускает импорт данных моделей Ingredient и Tag из
    файла формата json.
    """

    def __init__(self, *args, **kwargs):
        self.models = {
            'ingredients.json': Ingredient,
            'tags.json': Tag,
        }
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, nargs='?',
                            default=settings.DEFAULT_IMPORT_LOCATIONS)

    def handle(self, *args, **options):
        if options['json_file'] == settings.DEFAULT_IMPORT_LOCATIONS:
            file_list = options['json_file'].split(',')

            for file in file_list:
                self.add_to_database(file + '.json')
        else:
            self.add_to_database(options['json_file'])

    def add_to_database(self, file_path):
        if not isfile(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден.'))
            return

        model = None

        for key, value in self.models.items():
            if key in file_path:
                model = value
                break

        if model is not None:
            with open(file_path, encoding='utf-8') as file:
                data_list = json.load(file)

            model.objects.bulk_create([
                model(**data) for data in data_list
            ], ignore_conflicts=True)
        if model == Ingredient:
            self.stdout.write(
                self.style.SUCCESS('Объекты добавлены в базу данных '
                                   'для модели Ингредиент.'))
        elif model == Tag:
            self.stdout.write(
                self.style.SUCCESS('Объекты добавлены в базу данных '
                                   'для модели Тэг.'))
