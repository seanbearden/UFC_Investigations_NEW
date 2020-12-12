import json
from urllib.request import urlopen, Request
from urllib.error import URLError
from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime
from os import getcwd, makedirs
from os.path import exists, join


def get_soup(url):
    """Get html from url and return as BeautifulSoup

    Parameters
    ----------
    url : str
        url for webpage to be scraped.

    Returns
    -------
    bs4.BeautifulSoup
        soup of html

    """
    while True:
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            sleep(0.2)
            response = urlopen(request)
            break
        except URLError as err:
            print("URLError happened:", err)
            print('Trying again...')
            sleep(5)

    url_req = response.read()
    soup = BeautifulSoup(url_req, 'html.parser')
    response.close()
    return soup


def get_attribute_list(link_soup, attr):
    """Get atrributes from list of BeautifulSoup tags

    Parameters
    ----------
    link_soup : list
        List of bs4.element.Tag.
    attr : str
        html attribute to be selected.

    Returns
    -------
    list of str
        list of desired attributes.
    """
    return list(map(lambda line: line[attr], link_soup))


def strip_strs(str_list):
    """Strip list of strings of leading and trailing whitespace.

    Parameters
    ----------
    str_list : list
        List of strings.

    Returns
    -------
    list of str
    """
    return list(map(lambda x: x.text.strip(), str_list))


def get_ufcstats_event_links(stats_link="http://ufcstats.com/statistics/events/completed?page=all"):
    """Retrieve html, parse html for event links, and return links.
    Note that no data exists for UFC 1.

    Parameters
    ----------
    stats_link : str, optional
        Assuming the domain for UFCStats will not change

    Returns
    -------
    list of str
        List of urls to all events

    Notes
    -----
    The function returns the next upcoming event.
    """
    soup = get_soup(stats_link)
    matchup_links = soup.select("i.b-statistics__table-content > a[href]")
    matchup_links = get_attribute_list(matchup_links, 'href')
    return matchup_links


def get_ufcstats_matchup_links(ufcstats_event_url):
    """Retrieve and parse html for matchup urls for event

    Parameters
    ----------
    ufcstats_event_url : str

    Returns
    -------
    matchup_links : list
        list of url strings
    event_dict : dict
        Info for entire event
    """
    soup = get_soup(ufcstats_event_url)
    matchup_links = soup.select("tbody.b-fight-details__table-body > tr[data-link]")
    matchup_links = get_attribute_list(matchup_links, 'data-link')
    event_name = soup.select("body > section > div > h2 > span")
    event_info = soup.select("div.b-list__info-box.b-list__info-box_style_large-width > ul > li")
    event_name = event_name[0].text.strip()
    event_date = event_info[0].text.split(':')[1].strip()
    event_location = event_info[1].text.split(':')[1].strip()
    fight_count = len(matchup_links)
    event_dict = {'EventName': event_name,
                  'EventDate': event_date,
                  'EventLocation': event_location,
                  'EventURL': ufcstats_event_url,
                  'FightCount': fight_count}
    print(event_name, event_date, event_location)
    return matchup_links, event_dict


def parse_ufcstats_matchup(matchup_link):
    """Parse matchup html for info on fighters.

    Parameters
    ----------
    matchup_link : str
        url to matchup

    Returns
    -------
    dict
    """
    soup = get_soup(matchup_link)

    fighter_links = soup.select("h3.b-fight-details__person-name > a[href]")
    fighter_links = get_attribute_list(fighter_links, 'href')
    fighter_names = soup.select("h3.b-fight-details__person-name > a")
    fighter_names = strip_strs(fighter_names)
    nicknames = soup.select("div.b-fight-details__persons.clearfix > div.b-fight-details__person > div > p")
    nicknames = strip_strs(nicknames)
    outcomes = soup.select("div.b-fight-details__persons.clearfix > div.b-fight-details__person > i")
    outcomes = strip_strs(outcomes)
    bout_type = soup.select("div.b-fight-details__fight > div.b-fight-details__fight-head > i")
    special_bouts = bout_type[0].select('img')
    title_bout = False
    bonus = ''
    if special_bouts:
        for s in special_bouts:
            special_png_name = s['src'].split('/')[-1]
            if special_png_name == 'belt.png':
                title_bout = True
            elif special_png_name == 'perf.png':
                bonus += 'perf '
            elif special_png_name == 'fight.png':
                bonus += 'fight '
            elif special_png_name == 'sub.png':
                bonus += 'sub '
            elif special_png_name == 'ko.png':
                bonus += 'ko '
    perf_bonus = True if bonus else False
    bout_type = strip_strs(bout_type)[0]
    method = soup.select("div.b-fight-details__fight > div.b-fight-details__content > p:nth-child(1) > "
                         "i.b-fight-details__text-item_first > i:nth-child(2)")
    method = strip_strs(method)[0]
    round_seen = soup.select(
        "div.b-fight-details__fight > div.b-fight-details__content > p:nth-child(1) > i:nth-child(2)")
    round_seen = round_seen[0].text.split('Round:')[1].strip()
    round_time = soup.select(
        "div.b-fight-details__fight > div.b-fight-details__content > p:nth-child(1) > i:nth-child(3)")
    round_time = round_time[0].text.split('Time:')[1].strip()
    round_format = soup.select(
        "div.b-fight-details__fight > div.b-fight-details__content > p:nth-child(1) > i:nth-child(4)")
    round_format = round_format[0].text.split(':')[1].strip()
    referee = soup.select(
        "div.b-fight-details__fight > div.b-fight-details__content > p:nth-child(1) > i:nth-child(5) > span")
    referee = strip_strs(referee)[0]
    details = soup.select("div.b-fight-details__fight > div.b-fight-details__content > p:nth-child(2)")
    details = details[0].text.split('Details:')[1].strip()

    # TOTALS
    fighter_totals = soup.select("body > section > div > div > section:nth-child(4) > table > tbody > tr")
    round_totals = soup.select("body > section > div > div > section:nth-child(5) > table > tbody")
    fighter_strike_totals = soup.select("body > section > div > div > table > tbody > tr")
    round_strike_totals = soup.select("body > section > div > div > section:nth-child(8) > table > tbody")
    # check that data for rounds is available
    if round_totals:
        round_numbers = strip_strs(round_totals[0].select('th'))
        number_rounds_needed = len(round_numbers)
        subtotals = fighter_totals[0].select('td')
        round_subtotals = round_totals[0].select('td')
        strike_subtotals = fighter_strike_totals[0].select('td')
        round_strike_subtotals = round_strike_totals[0].select('td')

        fighter_0 = []
        fighter_1 = []
        fighter_0_rounds = []
        fighter_1_rounds = []
        fighter_0_strike_rounds = []
        fighter_1_strike_rounds = []
        for sub in subtotals + strike_subtotals:
            sub_p = sub.select('p')
            fighter_0.append(sub_p[0].text.strip())
            fighter_1.append(sub_p[1].text.strip())
        for sub in round_subtotals:
            sub_p = sub.select('p')
            fighter_0_rounds.append(sub_p[0].text.strip())
            fighter_1_rounds.append(sub_p[1].text.strip())
        for sub in round_strike_subtotals:
            sub_p = sub.select('p')
            fighter_0_strike_rounds.append(sub_p[0].text.strip())
            fighter_1_strike_rounds.append(sub_p[1].text.strip())

        # assert fighter_names[0] == fighter_0[0]
        # assert fighter_names[1] == fighter_1[0]
        # there are 10 strs of data per round
        # assert len(fighter_0_rounds) == len(round_numbers) * 10

        fighter_0_dict = {'Name': fighter_names[0],
                          'Opponent': fighter_names[1],
                          'Nickname': nicknames[0],
                          'Outcome': outcomes[0],
                          'UFCStats_Link': fighter_links[0],
                          'KD': fighter_0[1],
                          'SigStr': fighter_0[2],
                          'SigStrPerc': fighter_0[3],
                          'TotalStr': fighter_0[4],
                          'TD': fighter_0[5],
                          'TDPerc': fighter_0[6],
                          'SubAtt': fighter_0[7],
                          'Rev': fighter_0[8],
                          'Ctrl': fighter_0[9],
                          'Head': fighter_0[13],
                          'Body': fighter_0[14],
                          'Leg': fighter_0[15],
                          'Distance': fighter_0[16],
                          'Clinch': fighter_0[17],
                          'Ground': fighter_0[18],
                          'Round 1': {},
                          'Round 2': {},
                          'Round 3': {},
                          'Round 4': {},
                          'Round 5': {}}
        fighter_1_dict = {'Name': fighter_names[1],
                          'Opponent': fighter_names[0],
                          'Nickname': nicknames[1],
                          'Outcome': outcomes[1],
                          'UFCStats_Link': fighter_links[1],
                          'KD': fighter_1[1],
                          'SigStr': fighter_1[2],
                          'SigStrPerc': fighter_1[3],
                          'TotalStr': fighter_1[4],
                          'TD': fighter_1[5],
                          'TDPerc': fighter_1[6],
                          'SubAtt': fighter_1[7],
                          'Rev': fighter_1[8],
                          'Ctrl': fighter_1[9],
                          'Head': fighter_1[13],
                          'Body': fighter_1[14],
                          'Leg': fighter_1[15],
                          'Distance': fighter_1[16],
                          'Clinch': fighter_1[17],
                          'Ground': fighter_1[18],
                          'Round 1': {},
                          'Round 2': {},
                          'Round 3': {},
                          'Round 4': {},
                          'Round 5': {}}

        for i, r in enumerate(round_numbers):
            temp_0 = {'Name': fighter_0_rounds[i * 10 + 0],
                      'KD': fighter_0_rounds[i * 10 + 1],
                      'SigStr': fighter_0_rounds[i * 10 + 2],
                      'SigStrPerc': fighter_0_rounds[i * 10 + 3],
                      'TotalStr': fighter_0_rounds[i * 10 + 4],
                      'TD': fighter_0_rounds[i * 10 + 5],
                      'TDPerc': fighter_0_rounds[i * 10 + 6],
                      'SubAtt': fighter_0_rounds[i * 10 + 7],
                      'Rev': fighter_0_rounds[i * 10 + 8],
                      'Ctrl': fighter_0_rounds[i * 10 + 9],
                      'Head': fighter_0_strike_rounds[i * 9 + 3],
                      'Body': fighter_0_strike_rounds[i * 9 + 4],
                      'Leg': fighter_0_strike_rounds[i * 9 + 5],
                      'Distance': fighter_0_strike_rounds[i * 9 + 6],
                      'Clinch': fighter_0_strike_rounds[i * 9 + 7],
                      'Ground': fighter_0_strike_rounds[i * 9 + 8]
                      }
            temp_1 = {'Name': fighter_1_rounds[i * 10 + 0],
                      'KD': fighter_1_rounds[i * 10 + 1],
                      'SigStr': fighter_1_rounds[i * 10 + 2],
                      'SigStrPerc': fighter_1_rounds[i * 10 + 3],
                      'TotalStr': fighter_1_rounds[i * 10 + 4],
                      'TD': fighter_1_rounds[i * 10 + 5],
                      'TDPerc': fighter_1_rounds[i * 10 + 6],
                      'SubAtt': fighter_1_rounds[i * 10 + 7],
                      'Rev': fighter_1_rounds[i * 10 + 8],
                      'Ctrl': fighter_1_rounds[i * 10 + 9],
                      'Head': fighter_1_strike_rounds[i * 9 + 3],
                      'Body': fighter_1_strike_rounds[i * 9 + 4],
                      'Leg': fighter_1_strike_rounds[i * 9 + 5],
                      'Distance': fighter_1_strike_rounds[i * 9 + 6],
                      'Clinch': fighter_1_strike_rounds[i * 9 + 7],
                      'Ground': fighter_1_strike_rounds[i * 9 + 8]
                      }
            fighter_0_dict[r] = temp_0
            fighter_1_dict[r] = temp_1
    else:
        # Older events sometimes have missing info
        fighter_0_dict = {'Name': fighter_names[0],
                          'Opponent': fighter_names[1],
                          'Nickname': nicknames[0],
                          'Outcome': outcomes[0],
                          'UFCStats_Link': fighter_links[0],
                          'KD': '---',
                          'SigStr': '---',
                          'SigStrPerc': '---',
                          'TotalStr': '---',
                          'TD': '---',
                          'TDPerc': '---',
                          'SubAtt': '---',
                          'Rev': '---',
                          'Ctrl': '---',
                          'Head': '---',
                          'Body': '---',
                          'Leg': '---',
                          'Distance': '---',
                          'Clinch': '---',
                          'Ground': '---',
                          'Round 1': {},
                          'Round 2': {},
                          'Round 3': {},
                          'Round 4': {},
                          'Round 5': {}}
        fighter_1_dict = {'Name': fighter_names[1],
                          'Opponent': fighter_names[0],
                          'Nickname': nicknames[1],
                          'Outcome': outcomes[1],
                          'UFCStats_Link': fighter_links[1],
                          'KD': '---',
                          'SigStr': '---',
                          'SigStrPerc': '---',
                          'TotalStr': '---',
                          'TD': '---',
                          'TDPerc': '---',
                          'SubAtt': '---',
                          'Rev': '---',
                          'Ctrl': '---',
                          'Head': '---',
                          'Body': '---',
                          'Leg': '---',
                          'Distance': '---',
                          'Clinch': '---',
                          'Ground': '---',
                          'Round 1': {},
                          'Round 2': {},
                          'Round 3': {},
                          'Round 4': {},
                          'Round 5': {}}

    matchup_dict = {'Fighter_1': fighter_0_dict,
                    'Fighter_2': fighter_1_dict,
                    'WeightClass': bout_type,
                    'Bonus': perf_bonus,
                    'BonusType': bonus,
                    'Method': method,
                    'Round': round_seen,
                    'RoundTime': round_time,
                    'RoundFormat': round_format,
                    'Referee': referee,
                    'Details': details,
                    'TitleFight': title_bout}
    return matchup_dict


def write_event_links(event_links, stat_dir, event_links_txt):
    """ Save scraped event links to txt file

    Parameters
    ----------
    event_links : list
        links to be saved
    stat_dir : str
        directory name
    event_links_txt : str
        filename
    """
    with open(join(stat_dir, event_links_txt), 'w') as f:
        for s in event_links:
            f.write(str(s) + "\n")


def scrape_stats():
    """ Collect links to events, then scrape event information and save to json file.

    Returns
    -------
    bool
        determines if necessary to process jsons again

    """
    stat_dir = getcwd() + '/UFCStats_Dicts/'
    event_links_txt = 'event_links.txt'
    save_dir = join(stat_dir, 'All_Events/')
    if not exists(save_dir):
        makedirs(save_dir)

    event_links = get_ufcstats_event_links()
    # pop the upcoming event from list.
    upcoming_event = event_links.pop(0)
    if exists(join(stat_dir, event_links_txt)):
        event_links_stored = []
        with open(join(stat_dir, event_links_txt), 'r') as f:
            for line in f:
                event_links_stored.append(line.strip())

        temp_links = []
        for link in event_links:
            if link not in event_links_stored:
                temp_links.append(link)
        if temp_links:
            write_event_links(event_links, stat_dir, event_links_txt)
        event_links = temp_links

    else:
        write_event_links(event_links, stat_dir, event_links_txt)

    if event_links:
        need_to_process = True
        for j, event_link in enumerate(event_links):
            m_links, e_dict = get_ufcstats_matchup_links(event_link)
            for i, matchup_link in enumerate(m_links):
                sleep(0.1)
                bout_count = e_dict['FightCount'] - i
                m_dict = parse_ufcstats_matchup(matchup_link)
                e_dict[str(bout_count)] = m_dict

            dt = datetime.strptime(e_dict['EventDate'], '%B %d, %Y')

            filename = dt.strftime('%Y%m%d') + '_' + e_dict['EventName'].replace(" ", "") + '.json'

            json_object = json.dumps(e_dict, indent=4)
            with open(join(save_dir, filename), 'w') as outfile:
                outfile.write(json_object)
    else:
        need_to_process = False
    return need_to_process
