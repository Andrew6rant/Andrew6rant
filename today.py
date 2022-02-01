from datetime import datetime
from dateutil import relativedelta
from xml.dom import minidom

date1 = datetime(2002, 7, 5)
now = datetime.today()
date2 = datetime(now.year, now.month, now.day)

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


def svg_overwrite(filename):
    svg = minidom.parse(filename)
    f = open(filename, mode='w', encoding='utf-8')
    tspan = svg.getElementsByTagName('tspan')
    tspan[30].firstChild.data = daily_readme()
    f.write(svg.toxml("utf-8").decode("utf-8"))


if __name__ == '__main__':
    svg_overwrite("dark_mode.svg")
    svg_overwrite("light_mode.svg")
