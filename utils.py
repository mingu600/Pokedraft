import pandas as pd
from data import pokedex, learnsets, status_heal, momentum, priority_moves, immune_abilities, typechart, all_types, resist_convert
import numpy as np
from itertools import combinations
from collections import defaultdict
import heapq
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
  if val <= 0.25:
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
    M = (combinations(zip(total_df.pokemon, total_df.species, total_df.cost, total_df.types, total_df.stealthrock, total_df.spe),num_mons))
    groups = []
    for group in M:
        spec_set = set()
        mega_ctr = 0
        pkmn, cost, types, rocks, spe = [], [], set(), [], []
        for mon in group:
            pkmn.append(mon[0])
            spec_set.add(mon[1])
            if 'mega' in mon[0] and mon[0] != 'meganium':
                mega_ctr += 1
            cost.append(mon[2])
            for t in mon[3]:
                types.add(t)
            rocks.append(mon[4])
            spe.append(mon[5])
        if len(spec_set) < len(group) or mega_ctr > 1:
            continue
        groups.append((pkmn, cost, types, max(rocks), spe))
    return pd.DataFrame(groups,columns= ['pokemon', 'cost', 'types', 'stealthrock', 'spe'])


def restrictions(nec, total_df, config, nec_config=None):
    if nec:
        st.header("Necessary constraints for candidate Pokémon selection", divider='blue')
    else:
        st.header("Useful conditions for candidate Pokémon selection", divider='blue')
    if nec:
        nec_cost_bool = st.toggle("Cost restrictions", key=str(nec) + " cost toggle")
        if nec_cost_bool:
            nec_cost_start, nec_cost_end = st.select_slider(label="All candidate Pokémon need to be within this cost range.", options = range(min(total_df['cost']), max(total_df['cost']) + 1), value=[min(total_df['cost']), max(total_df['cost'])], key="nec cost")
            config["cost_range"] = (nec_cost_start, nec_cost_end)
    else:
       team_resist_bool = st.toggle("If turned on, candidate Pokémon will be evaluated alongside previously drafted Pokémon to check for any type weaknesses as a whole. Recommended to be turned on.", key=str(nec) + " cost toggle")
       if team_resist_bool:
            res_weight = st.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful resist weight")
            config["team_resists"] = res_weight


    nec_type_bool = st.toggle("Type restrictions", key=str(nec) + " type toggle")
    if nec_type_bool:
        if nec:
            nec_types= st.multiselect(label="At least one candidate Pokémon needs to be of these following types.", options = all_types, key="nec type")
            config["types"] = nec_types

        else:
            nec_types= st.multiselect(label= "At least one candidate Pokémon should be one of the following types.", options = all_types, key="useful type")
            type_weight = st.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful type weight")
            config["types"] = (nec_types, type_weight)
        
    if nec:
        rocks_bool = st.toggle("At least one candidate Pokémon needs to learn Stealth Rock", key=str(nec) + " rocks toggle")
        config["rocks"] = rocks_bool
    else:
        if not nec_config['rocks']:
            rocks_bool = st.toggle("If possible, at least one candidate Pokémon should learn Stealth Rock")
            if rocks_bool:
                rocks_weight = st.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful rocks weight")
                config["rocks"] = rocks_weight
    nec_speed_bool = st.toggle("Speed restrictions", key=str(nec) + " speed toggle")
    if nec_speed_bool:
        if nec:
            nec_speed_start, nec_speed_end = st.select_slider(label="At least one candidate Pokémon needs to be within this base speed range.", options = range(min(total_df['spe']), max(total_df['spe']) + 1), value=[min(total_df['spe']), max(total_df['spe'])], key="nec speed")
            config["speed_range"] = (nec_speed_start, nec_speed_end)
        else:
            nec_speed_start, nec_speed_end = st.select_slider(label="At least one candidate Pokémon should be within this base speed range.", options = range(min(total_df['spe']), max(total_df['spe']) + 1), value=[min(total_df['spe']), max(total_df['spe'])], key="useful speed")
            speed_weight = st.slider("How important is this condition? Weights are from 0 to 1.", min_value = 0., max_value = 1., value = 1., step = 0.1, key="useful speed weight")
            config["speed_range"] = ((nec_speed_start, nec_speed_end), speed_weight)
    return config


def _calculate_best_mons(next_df, config, useful_config, total_df, curr_team, others_drafted, keep_n=10):
    # NECESSARY CONFIG
    next_df = next_df[next_df['pokemon'].apply(lambda x: set(curr_team + others_drafted).isdisjoint(x))]
    # Cost range
    next_df = next_df[(next_df['cost'].apply(min) > config['cost_range'][0]) & (next_df['cost'].apply(max) < config['cost_range'][1])]
    # Types
    next_df = next_df[next_df['types'].apply(lambda x: set(config['types']).issubset(x))]
    # Rocks
    if config['rocks']:
        next_df = next_df[next_df['stealthrock'] == 1]
    # Speed range
    next_df = next_df[next_df['spe'].apply(lambda x: max(min(x), config['speed_range'][0]) <= min(max(x), config['speed_range'][1]))]
    heap = []

    for _, row in next_df.iterrows():
        score = 0
        if 'team_resists' in useful_config:
            new_team = curr_team + row['pokemon']
            score += useful_config['team_resists'] * np.exp(np.sum(np.clip(np.array(list(_evaluate_resists(total_df, new_team).values())), a_min = None, a_max=0)))

        if 'speed_range' in useful_config:
            speed_bool = 0
            config_vals = useful_config['speed_range']
            for spe in row['spe']:
                if spe >= config_vals[0] and spe <= config_vals[1]:
                    speed_bool = 1
                    break
            score += speed_bool * config_vals[2]

        if 'rocks' in useful_config:
            score += useful_config['rocks'] * row['stealthrock']

        if 'types' in useful_config:
            config_vals = useful_config['types']
            score += config_vals[1] * len(row['types'].intersection(config_vals[0])) / len(config_vals[0])

        heapq.heappush(heap, (score, tuple(row['pokemon'])))
    return heapq.nlargest(keep_n, heap)