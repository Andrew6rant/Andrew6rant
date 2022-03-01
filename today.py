import datetime
from dateutil import relativedelta
import requests
import os
from xml.dom import minidom

try: # This should run locally
    import config
    ACCESS_TOKEN = config.ACCESS_TOKEN
    OWNER_ID = config.OWNER_ID
except: # This should run on GitHub Actions
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
    OWNER_ID = os.environ['OWNER_ID']
HEADERS = {'authorization': 'token '+ ACCESS_TOKEN}


def daily_readme():
    """
    Returns the number of days since I was born
    """
    birth = datetime.datetime(2002, 7, 5)
    diff = relativedelta.relativedelta(datetime.datetime.today(), birth)
    return '{} {}, {} {}, {} {}'.format(diff.years, 'year' + format_plural(diff.years), diff.months, 'month' + format_plural(diff.months), diff.days, 'day' + format_plural(diff.days))


def format_plural(unit):
    """
    Returns a properly formatted number
    e.g.
    'day' + format_plural(diff.days) == 5
    >>> '5 days'
    'day' + format_plural(diff.days) == 1
    >>> '1 day'
    """
    if unit != 1:
        return 's'
    return ''


def graph_commits(start_date, end_date):
    """
    Uses GitHub's GraphQL v4 API to return my total commit count
    """
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
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=HEADERS)
    if request.status_code == 200:
        return int(request.json()['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])
    return 0


def graph_repos_stars(count_type, owner_affiliation):
    """
    Uses GitHub's GraphQL v4 API to return my total repository count, or a dictionary of the number of stars in each of my repositories
    This is a separate function from graph_commits, because graph_commits queries multiple times and this only needs to be ran once
    """
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation]) {
        user(login: "Andrew6rant") {
            repositories(first: 100, ownerAffiliations: $owner_affiliation) {
                totalCount
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            stargazers {
                                totalCount
                            }
                            owner {
                                id
                            }
                        }
                    }
                }
            }
        }
    }'''
    variables = {'owner_affiliation': owner_affiliation}
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=HEADERS)
    if request.status_code == 200:
        if count_type == "repos":
            return request.json()['data']['user']['repositories']['totalCount']
        else:
            return stars_counter(request.json()['data']['user']['repositories']['edges'])
    return 0


def stars_counter(data):
    """
    Count total stars in my repositories
    """
    total_stars = 0
    for node in data:
        total_stars += node['node']['stargazers']['totalCount']
    return total_stars


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data):
    """
    Parse SVG files and update elements with my age, commits, and stars
    """
    svg = minidom.parse(filename)
    f = open(filename, mode='w', encoding='utf-8')
    tspan = svg.getElementsByTagName('tspan')
    tspan[30].firstChild.data = age_data
    tspan[66].firstChild.data = commit_data
    tspan[68].firstChild.data = star_data
    tspan[70].firstChild.data = repo_data
    f.write(svg.toxml("utf-8").decode("utf-8"))


def commit_counter(date):
    """
    Counts up my total commits.
    Loops commits per year (starting backwards from today, continuing until my account's creation date)
    """
    total_commits = 0
    # since GraphQL's contributionsCollection has a maximum reach of one year
    while date.isoformat() > "2019-11-02T00:00:00.000Z": # one day before my very first commit
        old_date = date.isoformat()
        date = date - datetime.timedelta(days=365)
        total_commits += graph_commits(date.isoformat(), old_date)
    return total_commits


if __name__ == '__main__':
    """
    Runs program over each SVG image
    """
    age_data = daily_readme()
    commit_data = f'{commit_counter(datetime.datetime.today()): <12}'
    star_data = graph_repos_stars("stars", ["OWNER"])
    repo_data = f'{graph_repos_stars("repos", ["OWNER"]): <7}'

    svg_overwrite("dark_mode.svg", age_data, commit_data, star_data, repo_data)
    svg_overwrite("light_mode.svg", age_data, commit_data, star_data, repo_data)
