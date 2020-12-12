import json
import pandas as pd
from os import listdir, getcwd, makedirs
from os.path import isfile, join, exists


def find_weight_class(wc_str):
    """Determine the weight class of a fight by finding substring.

    If the weight class cannot be determined, the output will be 'UNKNOWN'.

    Parameters
    ----------
    wc_str : str

    Returns
    -------
    str
    """

    wcs = ['Strawweight', 'Flyweight', 'Bantamweight', 'Featherweight', 'Lightweight', 'Welterweight', 'Middleweight',
           'Light Heavyweight', 'Heavyweight', 'Open Weight', 'Tournament', 'Superfight', 'Catch Weight']
    for wc in wcs:
        if wc_str.find(wc) >= 0:
            return wc
    return 'UNKNOWN'


def process_jsons_into_csv(need_to_process):
    """ Load event data from jsons, process into matchups, then store all matchups in a single CSV file.

    Returns
    -------
    None
    """
    if need_to_process:
        all_events_dir = getcwd() + '/UFCStats_Dicts/All_Events/'
        processed_events_dir = getcwd() + '/UFCStats_Dicts/Processed/'
        if not exists(processed_events_dir):
            makedirs(processed_events_dir)
        processed_filename = 'All_Fights.csv'
        only_files = [f for f in listdir(all_events_dir) if isfile(join(all_events_dir, f)) and not f.startswith('.')]

        event_name = []
        event_date = []
        weight_class = []
        bonus_type = []
        bonus = []
        title = []
        method = []
        position_on_card = []
        round_seen = []
        round_time = []
        round_format = []
        fighter_1_name = []
        fighter_2_name = []
        fighter_1_outcome = []
        fighter_2_outcome = []
        for event_filename in only_files:
            with open(join(all_events_dir, event_filename)) as json_file:
                data = json.load(json_file)
                n_fights = data['FightCount']
                for fight_idx in range(1, n_fights + 1):
                    fight_idx_str = str(fight_idx)
                    position_on_card.append(fight_idx_str + ' of ' + str(n_fights))
                    event_name.append(data['EventName'])
                    event_date.append(data['EventDate'])
                    weight_class.append(find_weight_class(data[fight_idx_str]['WeightClass']))
                    bonus.append(data[fight_idx_str]['Bonus'])
                    bonus_type.append(data[fight_idx_str]['BonusType'])
                    title.append(data[fight_idx_str]['TitleFight'])
                    method.append(data[fight_idx_str]['Method'])
                    round_seen.append(data[fight_idx_str]['Round'])
                    round_time.append(data[fight_idx_str]['RoundTime'])
                    round_format.append(data[fight_idx_str]['RoundFormat'])
                    fighter_1_name.append(data[fight_idx_str]['Fighter_1']['Name'])
                    fighter_1_outcome.append(data[fight_idx_str]['Fighter_1']['Outcome'])
                    fighter_2_name.append(data[fight_idx_str]['Fighter_2']['Name'])
                    fighter_2_outcome.append(data[fight_idx_str]['Fighter_2']['Outcome'])

        d = {'EventName': event_name,
             'EventDate': event_date,
             'WeightClass': weight_class,
             'Bonus': bonus,
             'BonusType': bonus_type,
             'TitleFight': title,
             'Method': method,
             'Round': round_seen,
             'RoundTime': round_time,
             'RoundFormat': round_format,
             'FighterName1': fighter_1_name,
             'FighterName2': fighter_2_name,
             'FighterOutcome1': fighter_1_outcome,
             'FighterOutcome2': fighter_2_outcome,
             'CardPosition': position_on_card}

        df = pd.DataFrame(data=d)

        df['EventDate'] = pd.to_datetime(df['EventDate'])
        df.sort_values(by='EventDate', inplace=True)
        df.to_csv(join(processed_events_dir, processed_filename), index=False)
