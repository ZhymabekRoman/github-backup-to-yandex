# github-backup-to-yandex

`github-backup-to-yandex` - это скрипт на языке Python 3, который позволяет загрузить бэкап всего аккаунта GitHub в Яндекс.Диск. Скрипт может быть использован в GitHub Action.

## Зависимости:
- [python-github-backup](https://github.com/josegonzalez/python-github-backup) - утилита для бэкапирования GitHub.
- [yadisk](https://github.com/ivknv/yadisk) - бибилотека для работы с REST API Яндекс.Диска

## Параметры:
- `--github-token` - токен GitHub с необходимыми разрешениями для создания бэкапа (доступ к Gists, организациям, приватным репозиториям и т.д.).

- `--accounts` - аккаунты GitHub, которые требуется забэкапить. Формат значения: `user|ИмяПользователя org|НазваниеОрганизации`. Здесь `user` и `org` обозначают тип аккаунта, после символа `|` указывается имя пользователя или название организации. Список аккаунтов разделяется пробелами.

- `--yd-token` - токен Яндекс.Диска. Инструкцию по получению токена можно найти здесь: [ссылка на инструкцию](https://medium.com/@kai_kebutsuka/how-to-upload-files-to-yandex-disk-using-python-d3211007d574).
