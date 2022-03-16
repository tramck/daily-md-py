from dataclasses import dataclass
from datetime import date, timedelta
import os
from statistics import mean, median
from tabulate import tabulate

import click
from jinja2 import Template


DAILY_MD_CAL_LINK = os.environ['DAILY_MD_CAL_LINK']
DAILY_MD_DIRECTORY = os.environ['DAILY_MD_DIRECTORY']
TODAY = date.today()
ONE_DAY = timedelta(days=1)
TEMPLATE = '''
### TODO
{% for todo in todos %}
{{ todo }}{% endfor %}

{% if persistent_block %}
---
{{ persistent_block }}
{% endif %}
---

### Meeting Notes
'''


def file_for_day(day):
    return os.path.join(DAILY_MD_DIRECTORY, f'{day}.md')


def get_todos(day, complete=False):
    # get md file from previous day
    # parse to get unchecked todos
    # return unchecked todos
    previous_day_file = file_for_day(day)
    if not os.path.exists(previous_day_file):
        return []

    todo_marker = '- [x]' if complete else '- [ ]' 
    with open(previous_day_file) as f:
        return [
            line
            for line in f.readlines()
            if todo_marker in line
        ]



def get_persistent_block():
    start_marker = '<!-- PERSIST_START -->'
    end_marker = '<!-- PERSIST_END -->'

    previous_day_file = os.path.join(DAILY_MD_DIRECTORY, sorted(os.listdir(DAILY_MD_DIRECTORY))[-1])
    if not os.path.exists(previous_day_file):
        return ''
    with open(previous_day_file) as f:
        contents = f.read()
        if start_marker in contents and end_marker in contents:
            start = contents.find(start_marker)
            end = contents.find(end_marker) + len(end_marker)
            return contents[start:end]
        else:
            return ''


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
        todos=get_todos(TODAY - ONE_DAY) or ['new todo...'],
        persistent_block=get_persistent_block(),
    )
    with open(todays_file, 'w') as f:
        f.write(contents)
    click.echo(f'{todays_file} created!')


@dataclass
class Summary:
    days_worked: int
    complete_todos_count: int
    complete_todos_mean: float
    complete_todos_median: int
    # TODO: add support for:
    # days_to_complete_mean: float
    # days_to_complete_media: int
    # longest_open_todos: list[tuple[int, str]]


def get_summary(days, offset):
    day_range = range(0 - days - offset, offset)
    day_dates = [
        TODAY + timedelta(days=day_delta)
        for day_delta in day_range
    ]
    complete_todos_per_day = [
        get_todos(day, complete=True)
        for day in day_dates
        if os.path.exists(file_for_day(day))
    ]
    count_complete_todos_per_day = [
        len(todos) 
        for todos in complete_todos_per_day
    ]
    return Summary(
        days_worked=len(count_complete_todos_per_day),
        complete_todos_count=sum(count_complete_todos_per_day),
        complete_todos_mean=mean(count_complete_todos_per_day),
        complete_todos_median=median(count_complete_todos_per_day),
    )
    

def tabulate_summary(summary: Summary) -> str:
    return tabulate([
        [
            summary.complete_todos_count,
            summary.complete_todos_mean,
            summary.complete_todos_median,
        ]
    ], headers=["Total", "Average", "Median"], tablefmt="fancy_grid")


@cli.command(help='Display a summary of completed tasks')
@click.option('--days', default=7, help='Day window size.')
@click.option('--offset', default=0, help='Day window offset.')
def summary(days, offset):
    """
    Print total tasks completed, mean/median days to complete task, open long running tasks
    """
    _summary = get_summary(days, offset)

    print('\nDAYS WORKED:')
    print(_summary.days_worked)

    print('\nTODOS COMPLETE:')
    print(tabulate_summary(_summary))


if __name__ == '__main__':
    cli()