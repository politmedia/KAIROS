# KAIROS

KAIROS is a Voting Advice Application (VAA) which is developed and provided as an open source software. It allows you to run your own VAA with the views of politicians and parties to questions of a specific topic as a help to the voters.

KAIROS is a fork of [Freedomvote](https://github.com/freedomvote/freedomvote) with additional features. It is powered by [PolitMedia](https://www.politmedia.ch/). For more information, see [KAIROS.SOFTWARE](https://kairos.software/).

## Used in

- Swiss Election 2015 - [ch15.freedomvote.ch](https://ch15.freedomvote.ch/)
- Dutch Election 2017 - [freedomvote.nl](https://freedomvote.nl/)
- Swiss Election 2018 for the canton of bern - [ktbe18.freedomvote.ch](https://ktbe18.freedomvote.ch/)
- Swiss Election 2018 for the city of zurich - [stadtzh18.freedomvote.ch](https://stadtzh18.freedomvote.ch/)
- Swiss Election 2019 - [ch19.freedomvote.ch](https://ch19.freedomvote.ch/)

## How does it look?

This is how Freedomvote looked for the Swiss Election in 2015 - [freedomvote.ch](https://freedomvote.ch/)

![freedomvote.ch](https://raw.githubusercontent.com/freedomvote/freedomvote/master/tools/screenshot.png)

# Installation

## The "hard" way

Requirements:

- python 3
- postgresql (for SQLite see note below)
- libjpeg
- zlib
- python-pip

Run `pip install -r requirements.txt` to install all requirements.

Configure your DB settings and Secret in `app/settings.ini`:
There is an example in the `app/example.settings.ini`

**Please generate a new SECRET and don't commit it to your repository!**

More infos about the Django Secret
[Django Secret](https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-SECRET_KEY)

```ini
[DB]
NAME = freedomvote
USER = freedomvote
PASS = ***********
PORT = 5432
HOST = 127.0.0.1

[GLOBAL]
SECRET = GENERATE A SECRET
```

Edit the `tools/docker/cache_table.sql` file to change your database user, and
then run:

```bash
$ psql -h <db_host> -U <db_user> <db_name> < tools/docker/cache_table.sql
$ python app/manage.py migrate
$ python app/manage.py createsuperuser
$ python app/manage.py runserver
```

Now you can access the frontend on http://localhost:8000

## The easy way - Docker

To run Freedomvote in a docker container, you need to install docker and docker-compose and execute those commands:

```bash
$ make docker-init docker
```

Default user is `admin` with password `123qwe`, to change this, run `make docker-pw`

Now you can access the frontend on http://localhost:8000

## Development setup with SQLite

Add `DJANGO_DEBUG=1` to your environment to use a local SQLite database instead of Postgres. Not all features of the application may be available, as this is only partially supported, but you will have a functioning instance.

## Django management

Django already provides a number of [management commands](https://docs.djangoproject.com/en/1.10/ref/django-admin/) out of the box.
Other parts of this document already lists the usages of some of these commands.
Freedomvote provides a couple of custom commands to ease the setup process:

```bash
$ python app/manage.py help
$ python app/manage.py help <command>
$ python app/manage.py generate_politicians 42
$ python app/manage.py politician_import examples/politician_import.json
$ python app/manage.py user_import examples/user_import.json
```

# Languages

The whole application is multilingual. Per default the languages German, Italian and French are installed.
The translation are located in `app/locale/<lang_code>/LC_MESSAGES/django.po`. After editing the translation, run `python manage.py compilemessages`

To install another language (English in this example) make the following steps:

`app/freedomvote/settings.py`

```python
LANGUAGES = (
  ...
  ...
  ('en', _('english')),
)
```

then create a new folder for the language:

```bash
$ mkdir app/locale/en
```

now run those commands in your environment:

```bash
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py makemessages
$ python manage.py compilemessages
```

or with docker:

```bash
$ make docker-makemigrations
$ make docker-migrate
$ make docker-makemessages
$ make docker-compilemessages
```

# Translation

We use crowdin.com for translation. If you want to help us to translate Freedomvote into your language, head over to https://crowdin.com/project/freedomvote and start working :)

# License

GPLv3 see [LICENSE](https://github.com/freedomvote/freedomvote/blob/master/LICENSE)
