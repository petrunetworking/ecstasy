import pathlib
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import IO, List

from django.conf import settings

from check import models


@dataclass
class ConfigFile:
    """
    # Класс данных, представляющий файл конфигурации
    """

    name: str
    size: int
    modTime: str
    isDir: bool

    def __bool__(self):
        return bool(self.name)


class ConfigStorage(ABC):
    """
    Абстрактный класс для представления хранилища конфигурационных файлов
    """

    @abstractmethod
    def __init__(self, device: models.Devices):
        self.device = device

    @abstractmethod
    def check_storage(self) -> bool:
        """
        ## Проверяет, инициализирует или создает хранилище для оборудования.

        :return: OK?
        """
        pass

    @abstractmethod
    def open(self, file_name: str, mode: str = "rb", **kwargs) -> IO:
        """
        ## Открывает файл конфигурации

        :param file_name: Имя файла.
        :param mode: Режим доступа к файлу.
        :return: Объект `IO`.
        """
        pass

    @abstractmethod
    def delete(self, file_name: str) -> bool:
        """
        ## Удаляет файл конфигурации из хранилища

        :param file_name: Имя файла.
        :return: Удален?
        """
        pass

    @abstractmethod
    def files_list(self) -> List[ConfigFile]:
        """
        ## Возвращает список файлов конфигураций для оборудования

        :return: List[ConfigFile]
        """

        pass

    @abstractmethod
    def validate_config_name(self, file_name: str) -> bool:
        """
        ## Проверяет правильность имени файла конфигурации

        :param file_name: Имя файла.
        :return: OK?
        """
        pass

    @abstractmethod
    def is_exist(self, file_name: str) -> bool:
        """
        ## Проверяет наличие указанного файла конфигурации

        :param file_name: Имя файла.
        :return: Exist?
        """
        pass

    @abstractmethod
    def add(
        self, new_file_name: str, file_content=None, file_path: pathlib.Path = None
    ):
        """
        ## Добавляет новый файл конфигурации

        Необходимо указать названия файла, а также:

        - Содержимое файла (str или bytes)
        либо

        - Путь к имеющемуся файлу конфигурации для его последующего сохранения в хранилище


        :param new_file_name: Название файла в хранилище.
        :param file_content: Содержимое файла (optional).
        :param file_path: Путь к файлу (optional).
        """
        pass

    @staticmethod
    def slug_name(device_name: str) -> str:
        """
        Очищаем название оборудования от лишних символов

        Также переводит русские символы в английские. Заменяет пробелы на "_".
        Удаляет другие пробельные символы "\\t \\n \\r \\f \\v"

        Максимальная длина строки 220

        :param device_name: Название оборудования
        :return: Очищенное название
        """

        unicode_ascii = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "i",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "c",
            "ч": "cz",
            "ш": "sh",
            "щ": "scz",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "u",
            "я": "ja",
            "А": "A",
            "Б": "B",
            "В": "V",
            "Г": "G",
            "Д": "D",
            "Е": "E",
            "Ё": "E",
            "Ж": "ZH",
            "З": "Z",
            "И": "I",
            "Й": "I",
            "К": "K",
            "Л": "L",
            "М": "M",
            "Н": "N",
            "О": "O",
            "П": "P",
            "Р": "R",
            "С": "S",
            "Т": "T",
            "У": "U",
            "Ф": "F",
            "Х": "H",
            "Ц": "C",
            "Ч": "CZ",
            "Ш": "SH",
            "Щ": "SCH",
            "Ъ": "",
            "Ы": "y",
            "Ь": "",
            "Э": "E",
            "Ю": "U",
            "Я": "YA",
            " ": "_",
            "'": "/",
            "\\": "/",
            "[": "(",
            "]": ")",
            "{": "(",
            "}": ")",
            "—": "-",
        }

        ascii_str = ""
        for i in device_name:
            if i in unicode_ascii:
                ascii_str += unicode_ascii[i]
            elif i in string.whitespace:
                continue
            elif i.isascii():
                ascii_str += i

        return ascii_str


class LocalConfigStorage(ConfigStorage):
    """
    # Локальное хранилище для файлов конфигураций в директории
    """

    def __init__(self, device: models.Devices):
        self.device = device

        # Создание пути к каталогу, в котором хранятся файлы конфигурации.
        self._storage = pathlib.Path()
        self.check_storage()

    def check_storage(self) -> bool:
        # Проверяем наличие переменной
        if not settings.CONFIG_STORAGE_DIR or not isinstance(
            settings.CONFIG_STORAGE_DIR, pathlib.Path
        ):
            ValueError(
                "Укажите CONFIG_STORAGE_DIR в settings.py как объект `pathlib.Path`"
                " для использования локального хранилища конфигураций"
            )
        self._storage = settings.CONFIG_STORAGE_DIR / self.slug_name(self.device.name)
        # Создаем папку, если надо
        if not self._storage.exists():
            self._storage.mkdir(parents=True)
        return True

    def validate_config_name(self, file_name: str) -> bool:
        if ".." in file_name:
            return False

        return True

    def is_exist(self, file_name: str) -> bool:
        if not (self._storage / file_name).exists():
            return False
        return True

    def open(self, file_name: str, mode: str = "rb", **kwargs) -> IO:
        return (self._storage / file_name).open(mode, **kwargs)

    def delete(self, file_name: str) -> bool:
        (self._storage / file_name).unlink(missing_ok=True)
        return True

    def add(
        self, new_file_name: str, file_content=None, file_path: pathlib.Path = None
    ):

        # Если ничего не передали
        if not file_content and not file_path:
            return

        # Если передали только путь к файлу
        elif not file_content and file_path:
            with file_path.open("rb") as file:
                # Записываем содержимое файла
                file_content = file.read()

        # Выбираем флаги для записи
        if isinstance(file_content, str):
            mode = "w"
        else:
            mode = "wb"

        # Сохраняем файл
        with (self._storage / new_file_name).open(mode) as file:
            file.write(file_content)

    def files_list(self) -> List[ConfigFile]:
        config_files = sorted(
            self._storage.iterdir(),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        res = []
        # Итерируемся по всем файлам и поддиректориям в директории
        for file in config_files:
            # Получение статистики файла.
            stats = file.stat()
            res.append(
                ConfigFile(
                    name=file.name,
                    size=stats.st_size,  # Размер в байтах
                    modTime=datetime.fromtimestamp(stats.st_mtime).strftime(
                        "%H:%M %d.%m.%Y"  # Время последней модификации
                    ),
                    isDir=file.is_dir(),
                )
            )
        return res
