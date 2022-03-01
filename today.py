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
    raise Exception("the request has failed, graph_commits()")


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
            return all_repo_names(request.json()['data']['user']['repositories']['edges'])
    raise Exception("the request has failed, graph_repos_stars()")


def all_repo_names(data):
    """
    Returns the names of repos I have contributed to
    """
    total_loc = 0
    for node in data:
        name_with_owner = node['node']['nameWithOwner'].split('/')
        repo_name = name_with_owner[1]
        owner = name_with_owner[0]
        total_loc += graph_loc(owner, repo_name)
    return total_loc


def graph_loc(owner, repo_name, addition_total=0, cursor=None):
    query = '''
    query ($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            totalCount
                            edges {
                                node {
                                    ... on Commit {
                                        committedDate
                                    }
                                    author {
                                        user {
                                            id
                                        }
                                    }
                                    deletions
                                    additions
                                }
                                cursor
                            }
                        }
                    }
                }
            }
        }
    }'''
    variables = {"repo_name": repo_name, "owner": owner, "cursor": cursor}
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=HEADERS)
    if request.status_code == 200:
        return loc_counter_one_repo(owner, repo_name, request.json()['data']['repository']['defaultBranchRef']['target']['history']['edges'], addition_total, cursor)
    else:
        raise Exception("the request has failed, graph_loc()")


def loc_counter_one_repo(owner, repo_name, edges, addition_total, cursor=None, new_cursor="0"):
    if edges == []:
        return addition_total
    for node in edges:
        new_cursor = node['cursor'] # redefine cursor over and over again until it reaches the end
        if node['node']['author']['user'] == {'id': OWNER_ID}:
            addition_total += node['node']['additions']
    return graph_loc(owner, repo_name, addition_total, new_cursor)


def stars_counter(data):
    """
    Count total stars in my repositories
    """
    total_stars = 0
    for node in data:
        total_stars += node['node']['stargazers']['totalCount']
    return total_stars


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, total_loc):
    """
    Parse SVG files and update elements with my age, commits, and stars
    """
    svg = minidom.parse(filename)
    f = open(filename, mode='w', encoding='utf-8')
    tspan = svg.getElementsByTagName('tspan')
    tspan[30].firstChild.data = age_data
    tspan[65].firstChild.data = commit_data
    tspan[67].firstChild.data = star_data
    tspan[69].firstChild.data = repo_data
    tspan[71].firstChild.data = total_loc
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
    total_loc = "{:,}".format(graph_repos_stars("LOC", ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]))

    svg_overwrite("dark_mode.svg", age_data, commit_data, star_data, repo_data, total_loc)
    svg_overwrite("light_mode.svg", age_data, commit_data, star_data, repo_data, total_loc)
