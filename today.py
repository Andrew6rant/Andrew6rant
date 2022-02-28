import datetime
from dateutil import relativedelta
import requests
import os
from xml.dom import minidom

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']


def daily_readme():
    birth = datetime.datetime(2002, 7, 5)
    now = datetime.datetime.today()
    diff = relativedelta.relativedelta(now, birth)

    return '{} {}, {} {}, {} {}'.format(diff.years, 'year' + format_plural(diff.years), diff.months, 'month' + format_plural(diff.months), diff.days, 'day' + format_plural(diff.days))


def format_plural(unit):
    if unit != 1:
        return 's'
    return ''


def graph_commits(start_date, end_date):
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
    variables = {'start_date': start_date,'end_date': end_date}
    headers = {'authorization': 'token '+ ACCESS_TOKEN}
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=headers)
    if request.status_code == 200:
        return int(request.json()['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])
    return 0


def graph_repos_stars(count_type):
    # this is separate from graph_commits, because graph_commits queries multiple times
    query = '''
    {
    user(login: "Andrew6rant") {
        repositories(first: 100, ownerAffiliations: OWNER) {
            totalCount
            edges {
                node {
                    ... on Repository {
                        stargazers {
                            totalCount
                            }
                        }
                    }
                }
            }
        }
    }'''
    headers = {'authorization': 'token '+ ACCESS_TOKEN}
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        if count_type == "repos":
            return request.json()['data']['user']['repositories']['totalCount']
        else:
            return stars_counter(request.json()['data']['user']['repositories']['edges'])
    return 0


def stars_counter(data):
    total_stars = 0
    for node in data:
        total_stars += node['node']['stargazers']['totalCount']
    return total_stars


def svg_overwrite(filename):
    svg = minidom.parse(filename)
    f = open(filename, mode='w', encoding='utf-8')
    tspan = svg.getElementsByTagName('tspan')
    tspan[30].firstChild.data = daily_readme()
    tspan[66].firstChild.data = f'{commit_counter(datetime.datetime.today()): <12}'
    tspan[68].firstChild.data = graph_repos_stars("stars")
    tspan[70].firstChild.data = f'{graph_repos_stars("repos"): <7}'
    f.write(svg.toxml("utf-8").decode("utf-8"))


def commit_counter(date):
    total_commits = 0
    # since GraphQL's contributionsCollection has a maximum reach of one year
    while date.isoformat() > "2019-11-02T00:00:00.000Z": # one day before my very first commit
        old_date = date.isoformat()
        date = date - datetime.timedelta(days=365)
        total_commits += graph_commits(date.isoformat(), old_date)
    return total_commits


if __name__ == '__main__':
    svg_overwrite("dark_mode.svg")
    svg_overwrite("light_mode.svg")
