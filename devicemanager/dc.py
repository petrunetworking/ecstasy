"""
# Модуль для подключения к оборудованию через SSH, TELNET
"""
import re
from dataclasses import dataclass

import pexpect

from .exceptions import (
    TelnetConnectionError,
    DeviceLoginError,
    UnknownDeviceError,
    SSHConnectionError,
)
from .vendors import *


@dataclass
class SimpleAuthObject:
    login: str
    password: str
    secret: str = ""


class SSHSpawn:
    def __init__(self, ip, login):
        self.ip = ip
        self.login = login
        self.kex_algorithms = ""
        self.host_key_algorithms = ""
        self.ciphers = ""

    @staticmethod
    def _get_algorithm(output: str) -> str:
        algorithms = re.findall(r"Their offer: (\S+)", output)
        if algorithms:
            return algorithms[0]
        return ""

    def get_kex_algorithms(self, output: str):
        self.kex_algorithms = self._get_algorithm(output)

    def get_host_key_algorithms(self, output: str):
        self.host_key_algorithms = self._get_algorithm(output)

    def get_ciphers(self, output: str):
        self.ciphers = self._get_algorithm(output)

    def get_spawn_string(self) -> str:
        base = f"ssh -p 22 {self.login}@{self.ip}"

        if self.kex_algorithms:
            base += f" -oKexAlgorithms=+{self.kex_algorithms}"

        if self.host_key_algorithms:
            base += f" -oHostKeyAlgorithms=+{self.host_key_algorithms}"

        if self.ciphers:
            base += f" -c {self.ciphers}"

        return base

    def get_session(self):
        return pexpect.spawn(self.get_spawn_string(), timeout=15)


class DeviceFactory:
    """
    # Подключение к оборудованию, определение вендора и возврат соответствующего экземпляра класса
    """

    prompt_expect = r"[#>\]]\s*$"

    login_input_expect = (
        r"[Ll]ogin(?![-\siT]).*:\s*$|[Uu]ser\s(?![lfp]).*:\s*$|User:$|[Nn]ame.*:\s*$"
    )
    password_input_expect = r"[Pp]ass.*:\s*$"

    # Совпадения, после которых надо нажать `N` (no)
    send_N_key = r"The password needs to be changed|Do you want to see the software license"

    # Не доступен telnet
    telnet_unavailable = r"Connection closed|Unable to connect"

    telnet_authentication_expect = [
        login_input_expect,  # 0
        password_input_expect,  # 1
        prompt_expect,  # 2
        telnet_unavailable,  # 3
        r"Press any key to continue",  # 4
        r"Timeout or some unexpected error happened on server host",  # 5 - Ошибка радиуса
        send_N_key,  # 6 Нажать `N`
    ]

    def __init__(
        self,
        ip: str,
        protocol: str,
        snmp_community: str,
        auth_obj,
    ):
        self.ip = ip
        self.session = None
        self.snmp_community = snmp_community
        self.protocol = protocol

        if isinstance(auth_obj, list):
            self.login = []
            self.password = []
            # Список объектов
            for auth in auth_obj:
                self.login.append(auth.login)
                self.password.append(auth.password)
                self.privilege_mode_password = auth.secret

        else:
            # Один объект
            self.login = [auth_obj.login]
            self.password = [auth_obj.password]
            self.privilege_mode_password = auth_obj.secret

    def get_session(self) -> BaseDevice:
        return self._get_device_session()

    def __enter__(self) -> BaseDevice:
        """
        ## При входе в контекстный менеджер подключаемся к оборудованию.
        """
        return self._get_device_session()

    def _get_device_session(self) -> BaseDevice:
        if self.protocol == "ssh":
            self.session = self._connect_by_ssh()
        else:
            self.session = self._connect_by_telnet()
        return self.get_device(self.session)

    def get_device(self, session) -> BaseDevice:
        """
        # После подключения динамически определяем вендора оборудования и его модель

        Отправляем команду:

            # show version

        Ищем в выводе команды строчки, которые указывают на определенный вендор

        |           Вендор            |     Строка для определения    |
        |:----------------------------|:------------------------------|
        |             ZTE             |      " ZTE Corporation:"      |
        |           Huawei            |     "Unrecognized command"    |
        |            Cisco            |           "cisco"             |
        |          D-Link             |  "Next possible completions:" |
        |          Edge-Core          |      "Hardware version"       |
        |          Extreme            |          "ExtremeXOS"         |
        |           Q-Tech            |            "QTECH"            |
        |          Iskratel           |   "ISKRATEL" или "IskraTEL"   |
        |           Juniper           |            "JUNOS"            |
        |          ProCurve           |         "Image stamp:"        |

        """

        auth = {
            "login": self.login,
            "password": self.password,
            "privilege_mode_password": self.privilege_mode_password,
        }

        version = self.send_command(session, "show version")

        if "bad command name show" in version:
            version = self.send_command(session, "system resource print")

        # Mikrotik
        if "mikrotik" in version.lower():
            return MikroTik(session, self.ip, auth, snmp_community=self.snmp_community)

        # ProCurve
        if "Image stamp:" in version:
            return ProCurve(session, self.ip, auth, snmp_community=self.snmp_community)

        # ZTE
        if " ZTE Corporation:" in version:
            model = BaseDevice.find_or_empty(r"Module 0:\s*(\S+\s\S+);\s*fasteth", version)
            return ZTE(session, self.ip, auth, model=model, snmp_community=self.snmp_community)

        # HUAWEI
        if "Unrecognized command" in version:
            version = self.send_command(session, "display version")
            if "huawei" in version.lower():
                if "CX600" in version:
                    model = BaseDevice.find_or_empty(
                        r"HUAWEI (\S+) uptime", version, flags=re.IGNORECASE
                    )
                    return HuaweiCX600(session, self.ip, auth, model, self.snmp_community)
                if "quidway" in version.lower():
                    return Huawei(session, self.ip, auth, snmp_community=self.snmp_community)

            # Если снова 'Unrecognized command', значит недостаточно прав, пробуем Huawei
            if "Unrecognized command" in version:
                return Huawei(session, self.ip, auth, snmp_community=self.snmp_community)

        # CISCO
        if "cisco" in version.lower():
            model = BaseDevice.find_or_empty(r"Model number\s*:\s*(\S+)", version)
            return Cisco(session, self.ip, auth, model=model, snmp_community=self.snmp_community)

        # D-LINK
        if "Next possible completions:" in version:
            return Dlink(session, self.ip, auth, snmp_community=self.snmp_community)

        # Edge Core
        if "Hardware version" in version:
            return EdgeCore(session, self.ip, auth, snmp_community=self.snmp_community)

        # Eltex LTP
        if "Eltex LTP" in version:
            model = BaseDevice.find_or_empty(r"Eltex (\S+[^:\s])", version)
            if re.match(r"LTP-[48]X", model):
                return EltexLTP(
                    session, self.ip, auth, model=model, snmp_community=self.snmp_community
                )
            if "LTP-16N" in model:
                return EltexLTP16N(
                    session, self.ip, auth, model=model, snmp_community=self.snmp_community
                )

        # Eltex MES, ESR
        if "Active-image:" in version or "Boot version:" in version:
            eltex_device = EltexBase(session, self.ip, self.privilege_mode_password)
            if "MES" in eltex_device.model:
                return EltexMES(
                    eltex_device.session,
                    self.ip,
                    auth,
                    model=eltex_device.model,
                    mac=eltex_device.mac,
                    snmp_community=self.snmp_community,
                )
            if "ESR" in eltex_device.model:
                return EltexESR(
                    eltex_device.session,
                    self.ip,
                    auth,
                    model=eltex_device.model,
                    mac=eltex_device.mac,
                )

        # Extreme
        if "ExtremeXOS" in version:
            return Extreme(session, self.ip, auth)

        # Q-Tech
        if "QTECH" in version:
            model = BaseDevice.find_or_empty(r"\s+(\S+)\s+Device", version)
            return Qtech(session, self.ip, auth, model=model, snmp_community=self.snmp_community)

        # ISKRATEL CONTROL
        if "ISKRATEL" in version:
            return IskratelControl(
                session,
                self.ip,
                auth,
                model="ISKRATEL Switching",
                snmp_community=self.snmp_community,
            )

        # ISKRATEL mBAN>
        if "IskraTEL" in version:
            model = BaseDevice.find_or_empty(r"CPU: IskraTEL \S+ (\S+)", version)
            return IskratelMBan(
                session, self.ip, auth, model=model, snmp_community=self.snmp_community
            )

        if "JUNOS" in version:
            model = BaseDevice.find_or_empty(r"Model: (\S+)", version)
            return Juniper(session, self.ip, auth, model, snmp_community=self.snmp_community)

        if "% Unknown command" in version:
            session.sendline("display version")
            while True:
                match = session.expect([r"]$", "---- More", r">$", r"#", pexpect.TIMEOUT, "{"])
                if match == 5:
                    session.expect(r"\}:")
                    session.sendline("\n")
                    continue
                version += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                elif match == 4:
                    session.sendcontrol("C")
                else:
                    break
            if re.findall(r"VERSION : MA5600", version):
                model = BaseDevice.find_or_empty(r"VERSION : (MA5600\S+)", version)
                return HuaweiMA5600T(
                    session, self.ip, auth, model=model, snmp_community=self.snmp_community
                )

        if "show: invalid command, valid commands are" in version:
            session.sendline("sys info show")
            while True:
                match = session.expect([r"]$", "---- More", r">\s*$", r"#\s*$", pexpect.TIMEOUT])
                version += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                if match == 4:
                    session.sendcontrol("C")
                else:
                    break

        if "unknown keyword show" in version:
            return Juniper(session, self.ip, auth, snmp_community=self.snmp_community)

        raise UnknownDeviceError("Модель оборудования не была распознана", ip=self.ip)

    def _connect_by_ssh(self):
        connected = False
        session = None

        for login, password in zip(self.login + ["admin"], self.password + ["admin"]):

            try:
                ssh_spawn = SSHSpawn(ip=self.ip, login=self.login[0])
                session = ssh_spawn.get_session()

                while not connected:
                    expect_index = session.expect(
                        [
                            r"no matching key exchange method found",  # 0
                            r"no matching host key type found",  # 1
                            r"no matching cipher found|Unknown cipher",  # 2
                            r"Are you sure you want to continue connecting",  # 3
                            self.password_input_expect,  # 4
                            self.prompt_expect,  # 5
                            self.send_N_key,  # 6
                            r"Connection closed",  # 7
                            r"Incorrect login",  # 8
                            pexpect.EOF,  # 9
                        ],
                        timeout=30,
                    )

                    if expect_index == 0:
                        # KexAlgorithms
                        session.expect(pexpect.EOF)
                        ssh_spawn.get_kex_algorithms(session.before.decode("utf-8"))
                        session = ssh_spawn.get_session()

                    elif expect_index == 1:
                        # HostKeyAlgorithms
                        session.expect(pexpect.EOF)
                        ssh_spawn.get_host_key_algorithms(session.before.decode("utf-8"))
                        session = ssh_spawn.get_session()

                    elif expect_index == 2:
                        # Cipher
                        session.expect(pexpect.EOF)
                        ssh_spawn.get_ciphers(session.before.decode("utf-8"))
                        session = ssh_spawn.get_session()

                    elif expect_index == 3:
                        # Continue connection?
                        session.sendline("yes")

                    elif expect_index == 4:
                        session.send(password + "\r")

                    elif expect_index == 5:
                        # Got prompt
                        connected = True

                    elif expect_index == 6:
                        session.send("N\r")

                    elif expect_index == 8:
                        session.close()
                        raise DeviceLoginError(
                            "Неверный Логин/Пароль (подключение SSH)", ip=self.ip
                        )

                    elif expect_index in {7, 9}:
                        session.close()
                        raise SSHConnectionError("SSH недоступен", ip=self.ip)

                if connected:
                    self.login = login
                    self.password = password
                    break

            except Exception as exc:
                if session is not None and session.isalive():
                    session.close()
                raise exc

        return session

    def _connect_by_telnet(self):
        session = None
        try:
            session = pexpect.spawn(f"telnet {self.ip}", timeout=30)

            pre_set_index = None  # По умолчанию стартуем без начального индекса
            status = "Не был передал логин/пароль"
            for login, password in zip(self.login, self.password):

                status = self.__login_to_by_telnet(session, login, password, 30, pre_set_index)

                if status == "Connected":
                    # Сохраняем текущие введенные логин и пароль, они являются верными
                    self.login = login
                    self.password = password
                    break

                if "Неверный логин или пароль" in status:
                    pre_set_index = 0  # Следующий ввод будет логином
                    continue

            else:
                session.close()
                raise DeviceLoginError(status, ip=self.ip)

        except Exception as exc:
            if session is not None and session.isalive():
                session.close()
            raise exc

        return session

    def __login_to_by_telnet(
        self, session, login: str, password: str, timeout: int, pre_expect_index=None
    ) -> str:

        login_try = 1

        while True:
            # Ловим команды
            if pre_expect_index is not None:
                expect_index = pre_expect_index
                pre_expect_index = None

            else:
                expect_index = session.expect(self.telnet_authentication_expect, timeout=timeout)
            # Login
            if expect_index == 0:

                if login_try > 1:
                    # Если это вторая попытка ввода логина, то предыдущий был неверный
                    return f"Неверный логин или пароль (подключение telnet)"

                session.send(login + "\r")  # Вводим логин
                login_try += 1
                continue

            # Password
            if expect_index == 1:
                session.send(password + "\r")  # Вводим пароль
                continue

            # PROMPT
            if expect_index == 2:  # Если был поймал символ начала ввода команды
                return "Connected"

            # TELNET FAIL
            if expect_index == 3:
                raise TelnetConnectionError(f"Telnet недоступен", ip=self.ip)

            # Press any key to continue
            if expect_index == 4:  # Если необходимо нажать любую клавишу, чтобы продолжить
                session.send(" ")
                session.send(login + "\r")  # Вводим логин
                session.send(password + "\r")  # Вводим пароль
                session.expect(r"[#>\]]\s*")
                return "Connected"

            # Timeout or some unexpected error happened on server host' - Ошибка радиуса
            elif expect_index == 5:
                login_try = 1
                continue  # Вводим те же данные еще раз

            # The password needs to be changed
            if expect_index == 6:
                session.send("N\r")  # Не меняем пароль, когда спрашивает
                continue

            break

        return ""

    @staticmethod
    def send_command(session, command: str) -> str:
        """
        # Простой метод для отправки команды с постраничной записью вывода результата
        """

        session.send(command + "\r")
        version = ""
        while True:
            match = session.expect(
                [
                    r"]$",  # 0
                    r"-More-|-+\(more.*?\)-+",  # 1
                    r">\s*$",  # 2
                    r"#\s*",  # 3
                    pexpect.TIMEOUT,  # 4
                ],
                timeout=3,
            )

            version += str(session.before.decode("utf-8"))
            if match == 1:
                session.send(" ")
            elif match == 4:
                session.sendcontrol("C")
            else:
                break
        return version

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        ## При выходе из контекстного менеджера завершаем сессию
        """

        if self.session and self.session.isalive():
            self.session.close()
