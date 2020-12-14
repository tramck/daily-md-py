from datetime import date, timedelta
import os
import pytz

import click
from icalevents.icalevents import events
from jinja2 import Template


DAILY_MD_CAL_LINK = os.environ['DAILY_MD_CAL_LINK']
DAILY_MD_DIRECTORY = os.environ['DAILY_MD_DIRECTORY']
TODAY =  date.today()
ONE_DAY = timedelta(days=1)
YESTERDAY = TODAY - ONE_DAY
TOMORROW = TODAY + ONE_DAY
TEMPLATE = '''
### TODOs
{% for todo in todos %}
- [ ] {{ todo }}{% endfor %}
- [ ] new todo...

### Meeting Notes

{% for event in events %}#### {{ event['time'] }}: {{ event['summary'] }}
{% endfor %}
'''


def get_todays_calendar_events():
    start = TODAY
    end = TOMORROW
    es = events(os.environ['DAILY_MD_CAL_LINK'], start=start, end=end)
    latest_updated_event_by_uid = {}
    for event in es:
        uid = event.uid
        latest_seen_event = latest_updated_event_by_uid.get(uid)
        if (not latest_seen_event) or (latest_seen_event.last_modified < event.last_modified):
            latest_updated_event_by_uid[uid] = event
    return [
        {
            'time': event.start.astimezone(pytz.timezone('America/New_York')).strftime('%I:%M:%S %p'),
            'summary': event.summary,
        }
        for event in sorted(latest_updated_event_by_uid.values(), key=lambda event: event.start)
    ]


def file_for_day(day):
    return os.path.join(DAILY_MD_DIRECTORY, f'{day}.md')


def get_unfinished_todos():
    # get md file from yesterday
    # parse to get unchecked todos
    # return unchecked todos
    yesterdays_file = file_for_day(YESTERDAY)
    if not os.path.exists(yesterdays_file):
        return []

    todo_from_line = lambda line: line.replace('- [ ]', '')
    with open(yesterdays_file) as f:
        return [
            todo_from_line(line)
            for line in f.readline()
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
        events=get_todays_calendar_events(),
        todos=get_unfinished_todos(),
    )
    with open(todays_file, 'w') as f:
        f.write(contents)
    click.echo(f'{todays_file} created!')


if __name__ == '__main__':
    cli()