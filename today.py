from datetime import datetime
from dateutil import relativedelta
import requests
import os


date1 = datetime(2002, 7, 5)
now = datetime.today()
date2 = datetime(now.year, now.month, now.day)

diff = relativedelta.relativedelta(date2, date1)

years = diff.years
months = diff.months
days = diff.days


def dailyreadme():
    if years > 100:
        return 'null. I am dead"'
    elif days == 1:
        if months == 1:
            return '{} years, {} month, {} day"'.format(years, months, days)
        else:
            return '{} years, {} months, {} day"'.format(years, months, days)
    elif months == 1:
        return '{} years, {} month, {} days"'.format(years, months, days)
    elif days == 0:
        if months == 0:
            return '{} years"'.format(years)
        else:
            return '{} years, {} months"'.format(years, months, days)
    elif months == 0:
        return '{} years, {} days"'.format(years, days)
    else:
        return '{} years, {} months, {} days"'.format(years, months, days)


def converttuple(tup):
    con = ''.join(tup)
    return con


def readmeoverwrite():
    result = loc()
    print(result[1])
    current_line = 0
    current_line_art = ['  hNNNNNNMMMNNNNNNNNNNNMMMNNNmn       ', "'hNNNNNNmmmmmdddddhhdhhddmNMMMNN      ", ' dNNNNmso++/:///++oso+oossydNMMNy     ',
                        ' hNNNd/........----:/+oooossmMMNd     ', " 'hNN+.-+ssyyso:--/oyhhdhddhhMNNh     ", '  mNNshosooyddhyhydmmmddhhdmdNNN      ',
                        '  ddmoh--/+syysso/smddddhhyhhdmd      ', "  'so::---:/+++/../ydhhyyssssdh       ", '   o//`````...---./yyyyssooosd        ']
    with open("README.md", "r") as file:
        data = file.readlines()
        line4 = ('  :.```````````````````````--:     Uptime: "', dailyreadme(), "\n")
        line28 = ('    .dmmmNmNNNNNNNmmdhy.           Lines Written: ', str(result[0]), "\n")
        for lang in result[1]:
            temp_line = (current_line_art[current_line], str(lang).ljust(15, "."), ": ", str(result[1][lang]).rjust(5), "%\n")
            data[current_line+30] = converttuple(temp_line)
            current_line += 1
    data[4] = converttuple(line4)
    data[28] = converttuple(line28)

    with open('README.md', 'w') as file:
        file.writelines(data)


def lines_of_code(total):
    return total


def loc():
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
    total = 0
    private_total = 0
    language_holder = {}
    language_percentages = {}
    lines_not_counted = 0
    added_langs = 0
    final_lang_values = {}

    headers = {'authorization': 'token '+str(ACCESS_TOKEN)}
    # the url without html formatting is: api.github.com/search/repositories?q=user:andrew6rant is:private
    private_repos = requests.get('https://api.github.com/search/repositories?q=user%3Aandrew6rant%20is%3Aprivate', headers=headers).json()
    # Search is much more expensive API-wise, so I split up private and public repos
    public_repos = requests.get('https://api.github.com/users/Andrew6rant/repos', headers=headers).json()

    for iterable in public_repos:
        # I want every repo of mine except this. I did contribute to it, but it has over
        # 265,000 lines of JSON which throws off my calculations
        if iterable['full_name'] != 'Andrew6rant/ConsistencyPlus':
            online_loc = requests.get('https://api.codetabs.com/v1/loc?github='+iterable['full_name'])
            online_loc2 = online_loc.json()
            for language in online_loc2:
                if language['language'] == 'Total':
                    total += language['linesOfCode']
                elif language['language'] == 'License' or language['language'] == 'Markdown': # I don't want these counted either
                    lines_not_counted += language['linesOfCode']
                elif language['language'] in language_holder:
                    language_holder[language['language']] += language['linesOfCode']
                else:
                    language_holder[language['language']] = language['linesOfCode']

    for iterable in private_repos['items']:
        code_freq = requests.get('https://api.github.com/repos/' + iterable['full_name'] + '/stats/code_frequency', headers=headers).json()
        for lines in code_freq:
            # lines[0] is the id, [1] is the lines of code added, and [2] is lines removed (negative number)
            # I am not counting lines of code that were removed
            private_total += (lines[1] + lines[2])
    actual_total = f'{(total + private_total):,}'
    for key in language_holder:
        percentage = ((language_holder.get(key))/(total-lines_not_counted))*100
        language_percentages[key] = percentage
    toplangs = sorted(language_percentages, key=language_percentages.get, reverse=True)[:8]
    for lang in toplangs:
        added_langs += language_percentages[lang]
        final_lang_values[lang] = str(round(language_percentages[lang], 2))
    remaining_langs = round(100 - added_langs, 2)
    formatted_remainder = str(remaining_langs)
    print(str(remaining_langs))
    return actual_total, final_lang_values, formatted_remainder


if __name__ == '__main__':
    readmeoverwrite()
