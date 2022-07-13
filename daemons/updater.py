from os import environ
from time import sleep
from django import setup


def main():
    executable = ()
    while True:
        for exe in executable:
            exec_protected(exe)
        sleep(60)


if __name__ == '__main__':
    import sys
    sys.path.append('.')
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    setup()
    from bot.utils import exec_protected
    main()
