from datetime import date, timedelta
import os
import pytz

import click
from jinja2 import Template


DAILY_MD_CAL_LINK = os.environ['DAILY_MD_CAL_LINK']
DAILY_MD_DIRECTORY = os.environ['DAILY_MD_DIRECTORY']
TODAY = date.today()
ONE_DAY = timedelta(days=1)
TEMPLATE = '''
### TODO
{% for todo in todos %}
- [ ] {{ todo }}{% endfor %}

---

### Meeting Notes
'''


def file_for_day(day):
    return os.path.join(DAILY_MD_DIRECTORY, f'{day}.md')


def get_unfinished_todos():
    # get md file from previous day
    # parse to get unchecked todos
    # return unchecked todos
    previous_day_file = os.path.join(DAILY_MD_DIRECTORY, sorted(os.listdir(DAILY_MD_DIRECTORY))[-1])
    if not os.path.exists(previous_day_file):
        return []

    todo_from_line = lambda line: line.replace('- [ ] ', '')
    with open(previous_day_file) as f:
        return [
            todo_from_line(line)
            for line in f.readlines()
            if todo_from_line(line) != line
        ]


@click.group()
def cli():
    pass


@cli.command(help='Create a file from the calendar events for today and the incomplete TODOs from yesterday')
def new():
    todays_file = file_for_day(TODAY)
    if os.path.exists(todays_file):
        click.echo(f'{todays_file} already exists!')
        return

    template = Template(TEMPLATE)
    contents = template.render(
        todos=get_unfinished_todos() or ['new todo...'],
    )
    with open(todays_file, 'w') as f:
        f.write(contents)
    click.echo(f'{todays_file} created!')


if __name__ == '__main__':
    cli()