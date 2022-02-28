import datetime
from dateutil import relativedelta
import requests
import os
from xml.dom import minidom

date1 = datetime.datetime(2002, 7, 5)
now = datetime.datetime.today()
date2 = datetime.datetime(now.year, now.month, now.day)

diff = relativedelta.relativedelta(date2, date1)

years = diff.years
months = diff.months
days = diff.days


def daily_readme():
    return '{} {}, {} {}, {} {}'.format(years, 'year' + format_plural(years), months, 'month' + format_plural(months), days, 'day' + format_plural(days))


def format_plural(unit):
    if unit != 1:
        return 's'
    return ''


def graph_ql(query, start_date, end_date):
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
    variables = {'start_date': start_date,'end_date': end_date}
    headers = {'authorization': 'token '+ ACCESS_TOKEN}
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=headers)
    if request.status_code == 200:
        return int(request.json()['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])
    return 0


def svg_overwrite(filename):
    svg = minidom.parse(filename)
    f = open(filename, mode='w', encoding='utf-8')
    tspan = svg.getElementsByTagName('tspan')
    tspan[30].firstChild.data = daily_readme()
    tspan[66].firstChild.data = commit_counter(now)
    f.write(svg.toxml("utf-8").decode("utf-8"))


def commit_counter(date):
    query = '''
    query($start_date: DateTime!, $end_date: DateTime!) {
        user(login: "Andrew6rant") {
            contributionsCollection(from: $start_date, to: $end_date) {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }'''
    total_commits = 0
    # since GraphQL's contributionsCollection has a maximum reach of one year
    while date.isoformat() > "2019-11-02T00:00:00.000Z": # one day before my very first commit
        old_date = date.isoformat()
        date = date - datetime.timedelta(days=365)
        total_commits += graph_ql(query, date.isoformat(), old_date)
    return total_commits


if __name__ == '__main__':
    svg_overwrite("dark_mode.svg")
    svg_overwrite("light_mode.svg")
