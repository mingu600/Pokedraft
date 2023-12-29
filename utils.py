import pandas as pd
from data import pokedex, learnsets, status_heal, momentum, priority_moves, immune_abilities, typechart, all_types, resist_convert, image_url, res_to_chartval, stats, hazards, removal, cleric
from itertools import combinations
from collections import defaultdict
from bs4 import BeautifulSoup
import heapq
import numpy as np
import streamlit as st

def norm_name(name):
    return name\
        .replace(" ", "")\
        .replace("-", "")\
        .replace(".", "")\
        .replace("\'", "")\
        .replace("%", "")\
        .replace("*", "")\
        .replace(":", "")\
        .replace("&#39;", "") \
        .strip()\
        .lower()\
        .encode('ascii', 'ignore')\
        .decode('utf-8')
def preprocess_name(mon):
  if 'charizard' in mon.lower() and 'x' in mon.lower():
    mon = 'charizardmegax'
  elif 'charizard' in mon.lower() and 'y' in mon.lower():
    mon = 'charizardmegay'
  elif 'greninja' in mon.lower() and 'ash' in mon.lower():
    mon = 'greninjaash'
  elif mon[:2].lower() == 'g-':
    mon = mon[2:] + 'galar'
  elif mon[-2:].lower() == '-g':
    mon = mon[:-2] + 'galar'
  elif mon[:8].lower() == 'galarian':
    mon = mon[8:] + 'galar'
  elif mon[:5].lower() == 'galar':
    mon = mon[5:] + 'galar'

  elif mon[:2].lower() == 'a-':
    mon = mon[2:] + 'alola'
  elif mon[-2:].lower() == '-a':
    mon = mon[:-2] + 'alola'
  elif mon[:6].lower() == 'alolan':
    mon = mon[6:] + 'alola'
  elif mon[:5].lower() == 'alola':
    mon = mon[5:] + 'alola'

  elif mon[:2].lower() == 'm-':
    mon = mon[2:] + 'mega'
  elif mon[:2].lower() == 'm ':
    mon = mon[2:] + 'mega'
  elif mon[-2:].lower() == '-m':
    mon = mon[:-2] + 'mega'
  elif mon[:5].lower() == 'mega ':
    mon = mon[5:] + 'mega'

  elif mon[-2:].lower() == '-t':
    mon = mon[:-2] + 'therian'
  elif mon[-2:].lower() == '-i':
    mon = mon[:-2]
  elif mon[-10:].lower() == '-incarnate':
    mon = mon[:-10]

  elif mon[-7:].lower() == '-female':
    mon = mon[:-5]
  elif mon[-5:].lower() == '-male':
    mon = mon[:-3]

  elif mon[-7:].lower() == '-midday':
    mon = mon[:-7]

  return norm_name(mon)


def check_move(move, pokemon):
  if move in learnsets[pokemon]['learnset']:
    return 1
  return 0

def check_ability(ability, pokemon):
  if ability in pokedex[pokemon]['abilities'].values():
    return 1
  return 0

def _create_total_df(cost_dict):
    total = {}
    for pokemon in pokedex:
        if pokemon in cost_dict:
            if 'baseSpecies' in pokedex[pokemon]:
                species = pokedex[pokemon]['baseSpecies'].lower()
            else:
                species = pokemon
            total[pokemon] = [species]
            total[pokemon] += [pokedex[pokemon]['name']]
            total[pokemon] += [pokedex[pokemon]['num']]
            total[pokemon] += [cost_dict[pokemon]]
            total[pokemon] += [[x.lower() for x in pokedex[pokemon]['types']]]
            total[pokemon] += [pokedex[pokemon]['baseStats']['hp'], pokedex[pokemon]['baseStats']['atk'], pokedex[pokemon]['baseStats']['def'],
                            pokedex[pokemon]['baseStats']['spa'], pokedex[pokemon]['baseStats']['spd'], pokedex[pokemon]['baseStats']['spe']]
            learn_mon = pokemon
            if pokemon not in learnsets or 'learnset' not in learnsets[pokemon]:
                learn_mon = norm_name(pokedex[pokemon]['baseSpecies'])
            total[pokemon].append(check_move('stealthrock', learn_mon))
            total[pokemon].append(check_move('spikes', learn_mon))
            total[pokemon].append(check_move('toxicspikes', learn_mon))
            total[pokemon].append(check_move('stickyweb', learn_mon))
            total[pokemon].append(check_move('defog', learn_mon))
            total[pokemon].append(check_move('rapidspin', learn_mon))
            total[pokemon].append(check_move('wish', learn_mon))
            total[pokemon].append(0)
            for move in status_heal:
                if move in learnsets[learn_mon]['learnset']:
                    total[pokemon][-1] = 1
                    break
            total[pokemon].append(0)
            for move in momentum:
                if move in learnsets[learn_mon]['learnset']:
                    total[pokemon][-1] = 1
                    break
            total[pokemon].append(0)
            for move in priority_moves:
                if move in learnsets[learn_mon]['learnset']:
                    total[pokemon][-1] = 1
                    break
            for ability in immune_abilities:
                total[pokemon].append(check_ability(ability, pokemon))
    total_df = pd.DataFrame.from_dict(total, orient='index',
                                    columns=['species', 'name', 'num', 'cost', 'types', 'hp', "atk", "def", "spa", "spd", "spe", "stealthrock", "spikes", "toxicspikes",
                                            "stickyweb","defog","rapidspin","wish","statusheal", "momentum", "priority"] + [norm_name(x) for x in immune_abilities])
    total_df['pokemon'] = total_df.index
    return total_df

def ctr_convert(val):
  
  if val < 0.25:
    return 3
  elif val == 0.25:
    return 2
  elif val == 0.5:
    return 1
  elif val == 1:
    return 0
  else:
    return int(-1 * np.log2(val))

def update_resists(ctr, resists):
  for mon_type in ctr:
    resists[mon_type] += ctr_convert(ctr[mon_type])
  return resists

def _evaluate_resists(total_df, team):
  resists = defaultdict(int)
  for mon in team:
    ctr = defaultdict(lambda:1)
    row = total_df.loc[mon]
    for mon_type in row['types']:
      updates = typechart[mon_type.lower()]['damageTaken']
      for type_key in updates:
        if type_key.lower() in all_types:
          ctr[type_key.lower()] *= resist_convert[updates[type_key]]
    if row['dryskin'] == 1 or row['waterabsorb'] == 1 or row['stormdrain'] == 1:
      ctr['water'] = 0
    if row['heatproof'] == 1:
      ctr['fire'] /= 2
    if row['fluffy'] == 1:
      ctr['fire'] *= 2
    if row['flashfire'] == 1:
      ctr['fire'] = 0
    if row['levitate'] == 1:
      ctr['ground'] = 0
    if row['lightningrod'] == 1 or row['motordrive'] == 1 or row['voltabsorb'] == 1:
      ctr['electric'] = 0
    if row['sapsipper'] == 1:
      ctr['grass'] = 0
    resists = update_resists(ctr, resists)
  return resists

def _name_to_mon(total_df):
    name_map = {}
    for _, row in total_df.iterrows():
        name_map[row['name']] = row['pokemon']
    return name_map

def _create_group_df(total_df, num_mons):
    M = (combinations(zip(total_df.pokemon, total_df.species, total_df.cost, total_df.types, total_df.hp, total_df.atk, total_df['def'], total_df.spa,
                           total_df.spd, total_df.spe, total_df.stealthrock, total_df.spikes, total_df.toxicspikes, total_df.stickyweb, total_df.rapidspin, total_df.defog, 
                           total_df.wish, total_df.statusheal, total_df.momentum, total_df.priority),num_mons))
    groups = []
    for group in M:
        spec_set = set()
        mega_ctr = 0
        pkmn, cost, types, hp, atk, df, spa, spd, spe, rocks, spikes, tspikes, webs, spin, defog, wish, heal, mom, prio = [], [], set(), [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []
        for mon in group:
            pkmn.append(mon[0])
            spec_set.add(mon[1])
            if 'mega' in mon[0] and mon[0] != 'meganium':
                mega_ctr += 1
            cost.append(mon[2])
            for t in mon[3]:
                types.add(t)
            hp.append(int(mon[4]))
            atk.append(int(mon[5]))
            df.append(int(mon[6]))
            spa.append(int(mon[7]))
            spd.append(int(mon[8]))
            spe.append(int(mon[9]))
            rocks.append(mon[10])
            spikes.append(mon[11])
            tspikes.append(mon[12])
            webs.append(mon[13])
            spin.append(mon[14])
            defog.append(mon[15])
            wish.append(mon[16])
            heal.append(mon[17])
            mom.append(mon[18])
            prio.append(mon[19])
        if len(spec_set) < len(group) or mega_ctr > 1:
            continue
        groups.append((pkmn, cost, types, max(hp), max(atk), max(df), max(spa), max(spd) ,spe, max(rocks), max(spikes), max(tspikes), max(webs), max(spin),
                       max(defog), max(wish), max(heal), max(mom), max(prio)))
    return pd.DataFrame(groups,columns= ['pokemon', 'cost', 'types', 'hp', 'atk', 'def', 'spa', 'spd', 'spe', 'stealthrock',
                                         'spikes','toxicspikes','stickyweb','rapidspin','defog','wish','statusheal','momentum','priority'])


def restrictions(nec, total_df, config, col, num_mons, nec_config=None):
    if nec:
        col.header("Necessary constraints", divider='blue')
    else:
        col.header("Useful conditions", divider='blue')
    if nec:
        nec_cost_bool = col.toggle("Cost restrictions", key=str(nec) + " cost toggle")
        if nec_cost_bool:
            nec_cost_start, nec_cost_end = col.select_slider(label="Total cost of candidate Pokémon need to be within this cost range.", options = range(num_mons * min(total_df['cost']), num_mons * max(total_df['cost']) + 1), value=[num_mons * min(total_df['cost']), num_mons * max(total_df['cost'])], key="nec cost")
            config["cost_range"] = (nec_cost_start, nec_cost_end)

    else:
       team_resist_bool = col.toggle("If turned on, candidate Pokémon will be evaluated alongside previously drafted Pokémon to check for any type weaknesses as a whole. Recommended to be turned on.", key=str(nec) + " cost toggle")
       if team_resist_bool:
            res_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful resist weight")
            config["team_resists"] = res_weight

    col.write('')
    nec_type_bool = col.toggle("Type restrictions", key=str(nec) + " type toggle")
    if nec_type_bool:
        if nec:
            nec_types= col.multiselect(label="At least one candidate Pokémon needs to be of these following types.", options = all_types, key="nec type")
            config["types"] = nec_types

        else:
            nec_types= col.multiselect(label= "Ideally, at least one candidate Pokémon should be one of the following types.", options = all_types, key="useful type")
            type_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful type weight")
            config["types"] = (nec_types, type_weight)
    col.write('')


    nec_stat_bool = col.toggle("Stat restrictions (except speed)", key=str(nec) + " stat toggle")
    if nec_stat_bool:
        if nec:
            col.write("At least one candidate Pokémon has a high base stat value for the following stats:")
            stat_cols = col.columns([0.2, 0.2, 0.2, 0.2, 0.2])
            stat_names = ['HP', 'Atk', 'Def', 'SpA', 'SpD']
            for i in range(5):
                with stat_cols[i]:
                    stat_box = st.checkbox(f'{stat_names[i]}', key=str(nec) + stats[i])
                    if stat_box:
                        config[stats[i]] = stat_box
        else:
            col.write("At least one candidate Pokémon has a high base stat value for the following stats:")
            stat_cols = col.columns([0.2, 0.2, 0.2, 0.2, 0.2])
            stat_names = ['HP', 'Atk', 'Def', 'SpA', 'SpD']
            stat_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful stat weight")
            for i in range(5):
                with stat_cols[i]:
                    stat_box = st.checkbox(f'{stat_names[i]}', key=str(nec) + stats[i])
                    if stat_box:
                        config[stats[i]] = stat_weight
    col.write('')

    nec_speed_bool = col.toggle("Speed restrictions", key=str(nec) + " speed toggle")
    if nec_speed_bool:
        if nec:
            nec_speed_start, nec_speed_end = col.select_slider(label="At least one candidate Pokémon needs to be within this base speed range.", options = range(min(total_df['spe']), max(total_df['spe']) + 1), value=[min(total_df['spe']), max(total_df['spe'])], key="nec speed")
            config["speed_range"] = (nec_speed_start, nec_speed_end)
        else:
            nec_speed_start, nec_speed_end = col.select_slider(label="Ideally, at least one candidate Pokémon should be within this base speed range if possible.", options = range(min(total_df['spe']), max(total_df['spe']) + 1), value=[min(total_df['spe']), max(total_df['spe'])], key="useful speed")
            speed_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful speed weight")
            config["speed_range"] = ((nec_speed_start, nec_speed_end), speed_weight)

    col.write('')
    nec_hazard_bool = col.toggle("Hazard setting restrictions", key=str(nec) + " haz toggle")
    if nec_hazard_bool:
        if nec:
            col.write("At least one candidate Pokémon needs to learn the following hazards:")
            haz_cols = col.columns([0.3, 0.2, 0.25, 0.25])
            haz_names = ['Stealth Rock', 'Spikes', 'Toxic Spikes', 'Sticky Web']
            for i in range(4):
                with haz_cols[i]:
                    haz_box = st.checkbox(f'{haz_names[i]}', key=str(nec) + hazards[i])
                    if haz_box:
                        config[hazards[i]] = haz_box
        else:
            col.write("Ideally, at least one candidate Pokémon should learn the following hazards:")
            haz_cols = col.columns([0.3, 0.2, 0.25, 0.25])
            haz_names = ['Stealth Rock', 'Spikes', 'Toxic Spikes', 'Sticky Web']
            haz_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful haz weight")
            for i in range(4):
                with haz_cols[i]:
                    haz_box = st.checkbox(f'{haz_names[i]}', key=str(nec) + hazards[i])
                    if haz_box:
                        config[hazards[i]] = haz_weight
    col.write('')
    nec_removal_bool = col.toggle("Hazard removal restrictions", key=str(nec) + " rem toggle")
    if nec_removal_bool:
        if nec:
            col.write("At least one candidate Pokémon needs to learn the following hazard removal moves:")
            rem_cols = col.columns([0.5, 0.5])
            rem_names = ['Rapid Spin', 'Defog']
            for i in range(2):
                with rem_cols[i]:
                    rem_box = st.checkbox(f'{rem_names[i]}', key=str(nec) + removal[i])
                    if rem_box:
                        config[removal[i]] = rem_box
        else:
            col.write("Ideally, at least one candidate Pokémon should learn the following hazards:")
            rem_cols = col.columns([0.5, 0.5])
            rem_names = ['Rapid Spin', 'Defog']
            rem_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful rem weight")
            for i in range(2):
                with rem_cols[i]:
                    rem_box = st.checkbox(f'{rem_names[i]}', key=str(nec) + removal[i])
                    if rem_box:
                        config[removal[i]] = rem_weight
    col.write('')

    nec_cleric_bool = col.toggle("Cleric restrictions", key=str(nec) + " cleric toggle")
    if nec_cleric_bool:
        if nec:
            col.write("At least one candidate Pokémon needs to learn the following moves:")
            cleric_cols = col.columns([0.5, 0.5])
            cleric_names = ['Wish', 'Heal Bell/Aromatherapy']
            for i in range(2):
                with cleric_cols[i]:
                    cleric_box = st.checkbox(f'{cleric_names[i]}', key=str(nec) + cleric[i])
                    if cleric_box:
                        config[cleric[i]] = cleric_box
        else:
            col.write("Ideally, at least one candidate Pokémon needs to learn the following moves:")
            cleric_cols = col.columns([0.5, 0.5])
            cleric_names = ['Wish', 'Heal Bell/Aromatherapy']
            cleric_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful cleric weight")
            for i in range(2):
                with cleric_cols[i]:
                    cleric_box = st.checkbox(f'{cleric_names[i]}', key=str(nec) + cleric[i])
                    if cleric_box:
                        config[cleric[i]] = cleric_weight
    col.write('')

    if nec:
        mom_bool = col.toggle("At least one candidate Pokémon should have a momentum move (like U-turn)", key=str(nec) + " mom toggle")
        config["momentum"] = mom_bool
    elif not nec_config['momentum']:
        mom_bool = col.toggle("Ideally, at least one candidate Pokémon should have a momentum move (like U-turn)", key=str(nec) + " mom toggle")
        if mom_bool:
            mom_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful mom weight")
            config["momentum"] = mom_weight

    if nec:
        prio_bool = col.toggle("At least one candidate Pokémon should have a priority damaging move", key=str(nec) + " prio toggle")
        config["priority"] = prio_bool
    elif not nec_config['priority']:
        prio_bool = col.toggle("Ideally, at least one candidate Pokémon should have a priority damaging move", key=str(nec) + " prio toggle")
        if prio_bool:
            prio_weight = col.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful prio weight")
            config["priority"] = prio_weight

    return config


def _calculate_best_mons(next_df, config, useful_config, total_df, curr_team, others_drafted, keep_n=10):
    # NECESSARY CONFIG
    next_df = next_df[next_df['pokemon'].apply(lambda x: set(curr_team + others_drafted).isdisjoint(x))]
    # Cost range
    next_df = next_df[(next_df['cost'].apply(sum) >= config['cost_range'][0]) & (next_df['cost'].apply(sum) <= config['cost_range'][1])]
    # Stats
    for cond in stats:
        if config[cond]:
            if cond != 'hp':
                print(next_df[cond])
                next_df = next_df[next_df[cond] >= 110]
            else:
                next_df = next_df[next_df[cond] >= 90]
    # Speed range
    next_df = next_df[next_df['spe'].apply(lambda x: max(min(x), config['speed_range'][0]) <= min(max(x), config['speed_range'][1]))]
    # Types
    next_df = next_df[next_df['types'].apply(lambda x: not set(config['types']).isdisjoint(x))]
    # Hazards
    for hazard in hazards:
        if config[hazard]:
            next_df = next_df[next_df[hazard] == 1]
    # Removal
    for rem in removal:
        if config[rem]:
            next_df = next_df[next_df[rem] == 1]

    for cl in cleric:
        if config[cl]:
            next_df = next_df[next_df[cl] == 1]


    if config['momentum']:
       next_df = next_df[next_df['momentum'] == 1]

    if config['priority']:
       next_df = next_df[next_df['priority'] == 1]

    heap = []

    def boolCond(useful_config, row, cond):
       return useful_config[cond] * row[cond]

    for _, row in next_df.iterrows():
        score = 0
        if 'team_resists' in useful_config:
            new_team = curr_team + row['pokemon']
            score += useful_config['team_resists'] * np.exp(np.sum(np.clip(np.array(list(_evaluate_resists(total_df, new_team).values())), a_min = None, a_max=0)))

        if 'speed_range' in useful_config:
            speed_bool = 0
            config_vals = useful_config['speed_range']
            for spe in row['spe']:
                if spe >= config_vals[0][0] and spe <= config_vals[0][1]:
                    speed_bool = 1
                    break
            score += speed_bool * config_vals[1]


        for cond in stats:
            if cond in useful_config:
                if cond != 'hp':
                    if max(row[cond]) >= 110:
                        score += config_vals[0]
                else:
                    if max(row[cond]) >= 100:
                        score += config_vals[0]

        for cond in hazards:
            if cond in useful_config:
                score += boolCond(useful_config, row, cond)

        for cond in removal:
            if cond in useful_config:
                score += boolCond(useful_config, row, cond)

        for cond in cleric:
            if cond in useful_config:
                score += boolCond(useful_config, row, cond)

        for cond in ['momentum', 'priority']:
            if cond in useful_config:
                score += boolCond(useful_config, row, cond)

        if 'types' in useful_config:
            config_vals = useful_config['types']
            score += config_vals[1] * len(row['types'].intersection(config_vals[0])) / len(config_vals[0])

        heapq.heappush(heap, (score, tuple(row['pokemon'])))
    return heapq.nlargest(keep_n, heap)

def _gsheets(base, sheet):
   return f'https://docs.google.com/spreadsheets/d/{base}/gviz/tq?tqx=out:csv&sheet={sheet}'

def get_image(group, total_df):
    names = []
    images = []
    for mon in group:
        name = total_df.loc[mon]['name']
        pkmn = total_df.loc[mon]['pokemon']
        names.append(name)
        im_tag = '.png'
        if 'mega' in pkmn and pkmn != 'meganium':
            im_tag = '-m.png'
        elif 'hisui' in pkmn:
            im_tag = '-h.png'
        elif 'galar' in pkmn:
            im_tag = '-g.png'
        elif 'alola' in pkmn:
            im_tag = '-a.png'
        elif 'therian' in pkmn:
            if 'enamorus' in pkmn:
                im_tag = '-t.png'
            else:
                im_tag = '-s.png'
        elif pkmn == 'zygarde10':
            im_tag = '-10.png'
        elif pkmn == 'zygardecomplete':
            im_tag = '-c.png'
        elif pkmn == 'rotomwash':
            im_tag = '-w.png'
        elif pkmn == 'rotomfan':
            im_tag = '-s.png'
        elif pkmn == 'rotomheat':
            im_tag = '-h.png'
        elif pkmn == 'rotommow':
            im_tag = '-m.png'
        elif pkmn == 'rotomfrost':
            im_tag = '-f.png'
        images.append(image_url + str(total_df.loc[mon]['num']).zfill(3) +  im_tag)
    return names, images

# Converting links to html tags
def path_to_image_html(path):
    if path != 'Total:':
        return '<img src="' + path + '" width="60" >'
    return '<b>' + path + '</b>'

def _create_chart(curr_team, total_df):
    sprites = []
    speeds = []
    normal, fire, water, electric, grass, ice, fighting, poison, ground, flying, psychic, bug, rock, ghost, dragon , dark, steel, fairy = [],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]
    for mon in curr_team:
        resists = _evaluate_resists(total_df, [mon])
        _, image = get_image([mon], total_df)
        sprites += image
        speeds.append(total_df.loc[mon]['spe'])
        for ptype in resists:
           vars()[ptype].append(str(res_to_chartval[resists[ptype]]) + 'x')
    for i in range(2):
        sprites.append('')
        speeds.append('')
    sprites.append('Total:')
    speeds.append('')
    resists = _evaluate_resists(total_df, curr_team)
    for ptype in resists:
        for i in range(2):
            vars()[ptype].append('')
        vars()[ptype].append('+' + str(resists[ptype]))
    return sprites, speeds, normal, fire, water, electric, grass, ice, fighting, poison, ground, flying, psychic, bug, rock, ghost, dragon , dark, steel, fairy

def _create_team_chart(curr_team, total_df):
    sprites = []
    ability1 = []
    ability2 = []
    ability3 = []
    stealthrock = []
    spikes = []
    toxicspikes = []
    stickyweb = []
    defog = []
    rapidspin = []
    wish = []
    statusheal = []
    momentum = []
    priority = []
    def hasX(mon, lst, X):
        if total_df.loc[mon][X]:
            lst.append('✅')
        else:
            lst.append('❌')
        return lst

    for mon in curr_team:
        _, image = get_image([mon], total_df)
        sprites += image
        abilities = list(pokedex[mon]['abilities'].values())
        ability1.append(abilities[0])
        if len(abilities) > 1:
            ability2.append(abilities[1])
            if len(abilities) > 2:
              ability3.append(abilities[2])
            else:
              ability3.append('')
        else:
           ability2.append('')
           ability3.append('')
        stealthrock = hasX(mon, stealthrock, 'stealthrock')
        spikes = hasX(mon, spikes, 'spikes')
        toxicspikes = hasX(mon, toxicspikes, 'toxicspikes')
        stickyweb = hasX(mon, stickyweb, 'stickyweb')
        defog = hasX(mon, defog, 'defog')
        rapidspin = hasX(mon, rapidspin, 'rapidspin')
        wish = hasX(mon, wish, 'wish')
        statusheal = hasX(mon, statusheal, 'statusheal')
        momentum = hasX(mon, momentum, 'momentum')
        priority = hasX(mon, priority, 'priority')

    return sprites, ability1, ability2, ability3, stealthrock, spikes, toxicspikes, stickyweb, defog, rapidspin, wish, statusheal, momentum, priority


def change_color(html):
    soup = BeautifulSoup(html, 'html.parser')
    for cell in soup.find_all('td'):
        if 'img src' not in cell:
            cell['align'] = 'center'
            if 'x' in cell.text or '+' in cell.text:
                cell['style'] = 'background-color:' + cell_color(cell.text)
                if '+' in cell.text and cell.text[1] == '-':
                    cell.string = cell.text[1:]
            
    return soup


def cell_color(val):
    if val == '4x':
        color = '#990000'
    elif val == '2x':
        color = "#e06666"
    elif val == '1x':
        color = '#434343'
    elif val == '0x':
        color = '#000000'
    elif val == '0.5x':
        color = '#93c47d'
    elif val == '0.25x':
        color = '#38761d'
    elif '+' in val:
        num = float(val[1:])
        if num >= 2:
            color = '#38761d'
        elif num == 1:
            color = '#93c47d'
        elif num == 0:
            color = '#434343'
        elif num == -1:
            color = "#e06666"
        else:
            color = '#990000'

    else:
        color = '#38761d'
    return color
    #return '<i>' + val + '</i>'
    #return '<td style = "color:"' + color + ';>' + val + '</td>'