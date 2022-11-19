import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    range_to_numbers,
    _interface_normal_view,
    InterfaceList,
    InterfaceVLANList,
    MACList,
)


class EltexBase(BaseDevice):
    """
    # Для оборудования от производителя Eltex

    Промежуточный класс, используется, чтобы определить модель оборудования
    """

    prompt = r"\S+#\s*"
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    vendor = "Eltex"

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show system

          - MAC
          - Модель

        В зависимости от модели можно будет понять, какой класс для Eltex использовать далее

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """

        super().__init__(session, ip, auth, model)
        # Получение системной информации с устройства.
        system = self.send_command("show system")
        # Нахождение MAC-адреса устройства.
        self.mac = self.find_or_empty(r"System MAC [Aa]ddress:\s+(\S+)", system)
        # Регулярное выражение, которое ищет модель устройства.
        self.model = self.find_or_empty(
            r"System Description:\s+(\S+)|System type:\s+Eltex (\S+)", system
        )
        self.model = self.model[0] or self.model[1]

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        pass

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port: str, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass


class EltexMES(BaseDevice):
    """
    # Для оборудования от производителя Eltex серия **MES**

    Проверено для:
     - 2324
     - 3324
    """

    # Регулярное выражение, соответствующее началу для ввода следующей команды.
    prompt = r"\S+#\s*$"
    # Строка, которая отображается, когда вывод команды слишком длинный и не помещается на экране.
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    # Это переменная, которая используется для поиска файла шаблона для анализа вывода команды.
    _template_name = "eltex-mes"
    # Регулярное выражение, которое будет соответствовать MAC-адресу.
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Eltex"

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", mac=""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show inventory

          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """

        super().__init__(session, ip, auth, model)
        self.mac = mac
        inv = self.send_command("show inventory", expect_command=False)
        # Нахождение серийного номера устройства.
        self.serialno = self.find_or_empty(r"SN: (\S+)", inv)

    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования

        Выходим из режима конфигурирования:

            # end

        Сохраняем конфигурацию и подтверждаем

            # write
            Y

        Ожидаем ответа от оборудования **succeed**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        self.session.sendline("end")
        self.session.expect(self.prompt)
        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("write")
            self.session.expect("write")
            status = self.send_command("Y", expect_command=False)
            if "succeed" in status:
                return self.SAVED_OK

        return self.SAVED_ERR

    def get_interfaces(self) -> InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces description

        Считываем до момента вывода VLAN ```"Ch       Port Mode (VLAN)"```

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        self.session.sendline("show interfaces description")
        self.session.expect("show interfaces description")
        output = ""
        while True:
            # Ожидание prompt, space prompt или тайм-аута.
            match = self.session.expect(
                [self.prompt, self.space_prompt, pexpect.TIMEOUT]
            )
            output += self.session.before.decode("utf-8").strip()
            # Проверяем, есть ли в выводе строка "Ch Port Mode (VLAN)".
            # Если это так, он отправляем команду «q», а затем выходим из цикла.
            if "Ch       Port Mode (VLAN)" in output:
                self.session.sendline("q")
                self.session.expect(self.prompt)
                break
            if match == 0:
                break
            if match == 1:
                self.session.send(" ")
            else:
                print(self.ip, "Ошибка: timeout")
                break
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/{self._template_name}.template",
            "r",
            encoding="utf-8",
        ) as template_file:
            # используем TextFSM для анализа вывода команды.
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы

        return [
            (
                line[0],  # interface
                line[2].lower() if "up" in line[1].lower() else "admin down",  # status
                line[3],  # desc
            )
            for line in result
            if not line[0].startswith("V")  # Пропускаем Vlan интерфейсы
        ]

    def get_vlans(self) -> InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию

            # show running-config interface {interface_name}

        и выбираем строчки, в которых указаны VLAN:

         - ```vlan {vid}```
         - ```vlan add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', [vid:int, vid:int, ... vid:int] ), ... ]```
        """

        result = []
        interfaces = self.get_interfaces()
        for line in interfaces:
            if not line[0].startswith("V"):
                output = self.send_command(
                    f"show running-config interface {_interface_normal_view(line[0])}",
                    expect_command=False,
                )
                # Ищем все строки вланов в выводе команды
                vlans_group = re.findall(r"vlan [ad ]*(\S*\d)", output)
                port_vlans = []
                if vlans_group:
                    for v in vlans_group:
                        port_vlans += range_to_numbers(v)
                result.append((line[0], line[1], line[2], port_vlans))
        return result

    def get_mac(self, port) -> MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(
            f"show mac address-table interface {_interface_normal_view(port)}"
        )
        return re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str)

    def reload_port(self, port, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # configure terminal

        Переходим к интерфейсу:

            (config)# interface {port}

        Перезагружаем порт:

            (config-if)# shutdown
            (config-if)# no shutdown

        Выходим из режима конфигурирования:

            (config-if)# end

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("configure terminal")
        self.session.expect(r"#")
        self.session.sendline(f"interface {_interface_normal_view(port)}")
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.sendline("end")
        self.session.expect(r"#")
        r = self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return r + s

    def set_port(self, port, status, save_config=True):
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:
            # configure terminal

        Переходим к интерфейсу:
            (config)# interface {port}

        Меняем состояние порта:
            (config-if)# {shutdown|no shutdown}

        Выходим из режима конфигурирования:
            (config-if)# end

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("configure terminal")
        self.session.expect(r"\(config\)#")

        self.session.sendline(f"interface {_interface_normal_view(port)}")

        if status == "up":
            self.session.sendline("no shutdown")

        elif status == "down":
            self.session.sendline("shutdown")

        self.session.sendline("end")
        self.session.expect(r"#")

        r = self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @lru_cache
    def get_port_info(self, port):
        """
        ## Возвращает частичную информацию о порте.

        Пример

            Port: gi1/0/1
            Type: 1G-Fiber
            Link state: Up
            Auto negotiation: Enabled

        Через команду:

            # show interfaces advertise {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        info = self.send_command(
            f"show interfaces advertise {_interface_normal_view(port)}"
        ).split("\n")
        port_info_html = ""
        for line in info:
            if "Preference" in line:
                break
            port_info_html += f"<p>{line}</p>"

        return port_info_html

    @lru_cache
    def _get_port_stats(self, port):
        """
        ## Возвращает полную информацию о порте.

        Через команду:

            # show interfaces {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(
            f"show interfaces {_interface_normal_view(port)}"
        ).split("\n")

    def port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-FIBER", "COMBO-COPPER" или "?"
        """

        port_type = self.find_or_empty(r"Type: (\S+)", self.get_port_info(port))
        if "Fiber" in port_type:
            return "SFP"
        if "Copper" in port_type:
            return "COPPER"
        if "Combo-F" in port_type:
            return "COMBO-FIBER"
        if "Combo-C" in port_type:
            return "COMBO-COPPER"
        return "?"

    def port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}

        """

        return self.send_command(
            f"show running-config interface {_interface_normal_view(port)}"
        ).strip()

    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        port_info = self._get_port_stats(port)
        errors = []
        for line in port_info:
            if "error" in line:
                errors.append(line.strip())
        return "\n".join(errors)

    def set_description(self, port: str, desc: str) -> str:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Переходим в режим конфигурирования:

            # configure terminal

        Переходим к интерфейсу:

            (config)# interface {port}

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            (config-if)# no description

        Если **desc** содержит описание, то используем команду для изменения:

            (config-if)# description {desc}

        Выходим из режима конфигурирования:

            (config-if)# end

        Если длина описания больше чем разрешено на оборудовании, то выводим ```"Max length:{number}"```

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        desc = self.clear_description(desc)  # Очищаем описание

        # Переходим к редактированию порта
        self.session.sendline("configure terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {_interface_normal_view(port)}")
        self.session.expect(self.prompt)

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        if "bad parameter value" in res:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")
            return "Max length:" + self.find_or_empty(
                r" Up to (\d+) characters", output
            )

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'


class EltexESR(EltexMES):
    """
    # Для оборудования от производителя Eltex серия **ESR**

    Проверено для:
     - ESR-12VF
    """

    _template_name = "eltex-esr"

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", mac=""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show inventory

          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        :param mac: MAC адрес коммутатора
        """

        self.session: pexpect = session
        self.ip: str = ip
        self.auth: dict = auth
        self.model: str = model
        self.mac: str = mac
        system = self.send_command("show system")
        self.serialno: str = self.find_or_empty(r"serial number:\s+(\S+)", system)

    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования

        Для ESR необходимо сделать коммит конфигурации, а затем подтвердить её

            # commit
            # confirm

        Ожидаем ответа от оборудования **Configuration has been confirmed**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("commit")
        if (
            self.session.expect(
                [
                    self.prompt,  # 0
                    "Configuration has been successfully applied",  # 1
                    "Unknown command",  # 2
                ]
            )
            == 2  # Если неверная команда
        ):
            # Выходим из режима редактирования конфигурации
            self.session.sendline("end")
            self.session.sendline("commit")
            self.session.expect(
                [self.prompt, "Configuration has been successfully applied"]
            )

        # Подтверждаем изменение
        status = self.send_command("confirm")
        if "Configuration has been confirmed" in status:
            return self.SAVED_OK
        return self.SAVED_ERR

    def port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        Используется команда:

            # show interfaces sfp

        :param port: Порт для проверки
        :return: "SFP" или "COPPER"
        """

        if "SFP present" in self.send_command(
            f"show interfaces sfp {_interface_normal_view(port)}"
        ):
            return "SFP"
        return "COPPER"

    def get_port_info(self, port: str) -> str:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interfaces status {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(
            f"show interfaces status {_interface_normal_view(port)}",
            expect_command=False,
            before_catch=r"Description:.+",
        ).replace("\n", "<br>")

    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        Используется команда:

            # show interfaces counters

        :param port: Порт для проверки на наличие ошибок
        """

        port_stat = self.send_command(
            f"show interfaces counters {_interface_normal_view(port)}"
        ).split("\n")

        errors = ""
        for line in port_stat:
            if "errors" in line:
                errors += line.strip() + "\n"
        return errors
