#!/usr/bin/env python
"""Django's command-line tool. You run it like: python manage.py runserver"""
import os
import sys


def main():
    # Tell Django which settings file to use.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
