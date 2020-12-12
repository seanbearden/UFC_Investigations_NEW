import json
from urllib.request import urlopen, Request
from urllib.error import URLError
from bs4 import BeautifulSoup
from time import sleep
from os import getcwd, makedirs
from os.path import exists, join
from string import ascii_lowercase

# Need to remove DWCS fighters who have yet to compete in UFC
# Need UFC W/L record. Also finish info.

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
            sleep(0.1)
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


def get_ufcstats_fighter_links():
    """Retrieve html, parse html for fighter links, and return links.

    Returns
    -------
    list of str
        List of urls to all UFC fighters, past and present.
    """
    alphabet = list(ascii_lowercase)
    fighter_links = []
    for char in alphabet:
        stats_link = 'http://ufcstats.com/statistics/fighters?char=' + char + '&page=all'
        soup = get_soup(stats_link)

        fighter_links_temp = soup.select("td.b-statistics__table-col > a[href]")
        # could be two or three links that are the same due to nicknames.
        fighter_links += list(set(get_attribute_list(fighter_links_temp, 'href')))

    return fighter_links


def parse_ufcstats_fighter(fighter_link):
    """Parse html for info on fighter.

    Parameters
    ----------
    fighter_link : str
        url to fighter history

    Returns
    -------
    dict
    """
    soup = get_soup(fighter_link)

    fighter_name_text = soup.select("span.b-content__title-highlight")
    fighter_name = fighter_name_text[0].text.strip()
    fighter_record_text = soup.select("span.b-content__title-record")
    fighter_record = fighter_record_text[0].text.split(':')[1].strip()
    record = fighter_record.split('-')

    W = int(record[0])
    L = int(record[1])
    if 'NC' in record[2]:
        temp = record[2].split('(')
        D = int(temp[0])
        NC = int(temp[1][0])    # Assuming no fighter has more than 9 No Contests
        total_pro_fights = W + L + D + NC
    else:
        D = int(record[2])
        NC = 0
        total_pro_fights = W + L + D

    fighter_stats_text = soup.select("ul.b-list__box-list > li")
    height = fighter_stats_text[0].text.split(':')[1].strip()
    # height = height.split()
    # height = height[0].strip('\''))*12 + int(height[1].strip('\"')
    weight = fighter_stats_text[1].text.split(':')[1].strip().split()[0]
    reach = fighter_stats_text[2].text.split(':')[1].strip(' \n\"')
    stance = fighter_stats_text[3].text.split(':')[1].strip()
    DOB = fighter_stats_text[4].text.split(':')[1].strip()
    SLpM = fighter_stats_text[5].text.split(':')[1].strip()
    StrAcc = fighter_stats_text[6].text.split(':')[1].strip(' \n\%')
    SApM = fighter_stats_text[7].text.split(':')[1].strip()
    StrDef = fighter_stats_text[8].text.split(':')[1].strip(' \n\%')
    TDAvg = fighter_stats_text[10].text.split(':')[1].strip()
    TDAcc = fighter_stats_text[11].text.split(':')[1].strip(' \n\%')
    TDDef = fighter_stats_text[12].text.split(':')[1].strip(' \n\%')
    SubAvg = fighter_stats_text[13].text.split(':')[1].strip()

    fighter_ufc_history = soup.select("tbody.b-fight-details__table-body > tr")
    ufc_fight_count = 0
    next_fight = ''
    last_fight = ''
    if len(fighter_ufc_history) > 1:
        if fighter_ufc_history[1].text.split()[0] == 'next':
            ufc_fight_count = len(fighter_ufc_history) - 2
            next_fight = fighter_ufc_history[1].find_all('p')[5].text.strip()
            if ufc_fight_count > 0:
                last_fight = fighter_ufc_history[2].find_all('p')[12].text.strip()
        else:
            ufc_fight_count = len(fighter_ufc_history) - 1
            last_fight = fighter_ufc_history[1].find_all('p')[12].text.strip()



    fighter_dict = {'FighterStats': {
        'FighterName': fighter_name,
        'FighterLink': fighter_link,
        'LastFightDate': last_fight,
        'NextFightDate': next_fight,
        'W': W,
        'L': L,
        'D': D,
        'NC': NC,
        'TotalFights': total_pro_fights,
        'UFCFights': ufc_fight_count,
        'height': height,
        'weight': weight,
        'reach': reach,
        'stance': stance,
        'DOB': DOB,
        'SLpM': SLpM,
        'StrAcc': StrAcc,
        'SApM': SApM,
        'StrDef': StrDef,
        'TDAvg': TDAvg,
        'TDAcc': TDAcc,
        'TDDef': TDDef,
        'SubAvg': SubAvg
    }}
    return fighter_dict


def write_fighter_links(fighter_links, stat_dir, fighter_links_txt):
    """ Save scraped fighter links to txt file

    Parameters
    ----------
    fighter_links : list
        links to be saved
    stat_dir : str
        directory name
    fighter_links_txt : str
        filename
    """
    with open(join(stat_dir, fighter_links_txt), 'w') as f:
        for s in fighter_links:
            f.write(str(s) + "\n")


def scrape_stats():
    """ Collect links to UFC fighters, then scrape fighter information and save to json file.

    Returns
    -------
    bool
        determines if necessary to process jsons again
    """
    stat_dir = getcwd() + '/UFCStats_Dicts/'
    fighter_links_txt = 'fighter_links.txt'
    save_dir = join(stat_dir, 'All_Fighters/')
    if not exists(save_dir):
        makedirs(save_dir)
    if exists(join(stat_dir, fighter_links_txt)):
        fighter_links = []
        with open(join(stat_dir, fighter_links_txt), 'r') as f:
            for line in f:
                fighter_links.append(line.strip())
    else:
        fighter_links = get_ufcstats_fighter_links()
        write_fighter_links(fighter_links, stat_dir, fighter_links_txt)

    for f in fighter_links:
        print(f)
        f_dict = parse_ufcstats_fighter(f)
        filename = f_dict['FighterStats']['FighterName'].replace(' ', '_') + '_' + f.split('/')[-1] + '.json'
        print(filename)
        json_object = json.dumps(f_dict, indent=4)
        with open(join(save_dir, filename), 'w') as outfile:
            outfile.write(json_object)



if __name__ == '__main__':
    scrape_stats()
    # print(parse_ufcstats_fighter('http://ufcstats.com/fighter-details/5d1b7e3dd9e11074'))