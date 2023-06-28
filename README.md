# Ecstasy

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
[![Code style: black](https://img.shields.io/badge/code_style-black-black.svg)](https://github.com/psf/black)

<div>
<img src="https://www.vectorlogo.zone/logos/vuejs/vuejs-icon.svg" alt="vue.js" width="30" height="30"/>
<strong style="padding: 2px; vertical-align: text-bottom">+</strong>
<img src="https://cdn.worldvectorlogo.com/logos/django.svg" alt="django" width="30" height="30"/>
<strong style="padding: 2px; vertical-align: text-bottom">+</strong>
<img src="https://www.vectorlogo.zone/logos/redis/redis-icon.svg" alt="redis" width="32" height="32"/>
<strong style="padding: 2px; vertical-align: text-bottom">+</strong>
<img src="https://codeguida.com/media/post_title/celery-logo.png" alt="celery" width="32" height="32"/>
</div>

### Веб-приложение для взаимодействия с сетевым оборудованием

Позволяет отображать информацию о сетевых устройствах в удобном для чтения формате
без ввода консольных команд.


![img.png](img/img_3.png)

### Возможности:

- Взаимодействие с сетевым оборудованием
  - Отображение интерфейсов оборудования в реальном времени
  - Управление состоянием порта (up/down)
  - Просмотр MAC адресов на порту
  - Просмотр текущей конфигурации порта
  - Перенаправление для просмотра логов в Elastic Stack
  - Просмотр ошибок на порту
  - Возможность просматривать и сбрасывать текущую сессию по MAC адресу
  - Сохранение файлов конфигураций оборудования

Кроме того, Ecstasy предоставляет дополнительные функции для визуализации 
и поиска сетевой информации:

- Отображение топологии VLAN / MAC
- Поиск по текстовому описанию интерфейсов
- Поиск IP/MAC адреса
- Создание и просмотр интерактивных карт

### Поддержка производителей оборудования:

Список поддерживаемых вендоров приведен ниже. Другие модели тоже могут быть совместимы, но я имею доступ только к этим устройствам.
- `Cisco`
  - Проверено для: `WS-C4500*` `WS-C35*0` `WS-C3750*` `ME-3*00X` `ME-4924` `ME-3400`
- `Eltex`
  - Проверено для: `MES3324*` `ESR-12VF` `LTP-4X(8X)-rev.*` `LTP-16N`
- `MikroTik`
  - Проверено для: `RouterOS v6.* (v7.*)`
- `Huawei`
  - Проверено для: `S2403TP` `S2326TP` `CX600-X8`
- `Huawei DSL (GPON)`
  - Проверено для: `MA5600T`
- `Iskratel DSL`
  - Проверено для: `MPC8560`
- `D-Link`
  - Проверено для: `DES-3200-*` `DES-3028` `DES-3526` `DGS-3420` `DGS-12**`
- `Extreme`
  - Проверено для: `X460-*` `X670-*`
- `ZTE`
  - Проверено для: `ZXR10 2928E` `2936-FI` `2952E`
- `Q-Tech`
  - Проверено для: `QSW-3450-*` `QSW-8200-*`

## Структура

![img.png](img/img_8.png)

### Удобный поиск оборудования

![img.png](img/img_4.png)


### Просмотр загруженности интерфейсов оборудований

![img.png](img/img_9.png)


При выборе оборудования показывается его информация:

- Состояние оборудования
- Нагрузка CPU, RAM, Flash и температура
- Подробная информация (берется из Zabbix)
- Ссылка в Zabbix
- Ссылка на карту с местоположением оборудования
- Логи в Elastic Search
- Перечень конфигураций
- Медиафайлы
- Интерфейсы


![img.png](img/img.png)


При выборе конкретного порта открывается его информация:
Описание, конфигурация, счетчик ошибок, диагностика состояния кабеля, список VAC адресов

![img_1.png](img/img_1.png)

Для станционных терминалов GPON OLT возможен следующий вывод информации об интерфейсе (указан ниже)

![img.png](img/img_2.png)

## Карты

Реализована возможность отображать и создавать интерактивные карты:

- Из ссылки на внешнюю карту;
- Из HTML файла карты;
- Из совокупности различных слоев. Слой может быть представлен:
  - Из группы в Zabbix (будут отображаться узлы сети, которые имеют координаты);
  - Из файла формата GEOJSON.

Интерактивные карты со слоями из Zabbix группы отображают доступность оборудования 
с описанием проблемы в Zabbix.

![img.png](img/interactive-map.png)

## Топология VLAN

Построение топологии VLAN по оборудованию.

![img.png](img/img_6.png)

## Топология прохождения MAC адреса

Определение маршрута MAC адреса между оборудованиями.

![img.png](img/img_10.png)

## Поиск по описанию порта

![img.png](img/img_5.png)

### Поиск IP или MAC адреса

![img.png](img/img_7.png)

## Создание связей моделей

```shell
python manage.py graph_models -a --rankdir LR --dot -g -o ./docs/models.dot
dot -Tsvg ./docs/models.dot -o ./docs/models.svg
```
