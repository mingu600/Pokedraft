import json

with open('learnsets.json', 'r') as f:
  learnsets = json.load(f)
with open('pokedex.json', 'r', encoding="utf8") as f:
  pokedex = json.load(f)
with open('typechart.json', 'r') as f:
  typechart = json.load(f)

priority_moves = ['accelerock', 'aquajet','bulletpunch','extremespeed','fakeout','firstimpression','iceshard','machpunch','quickattack',
'shadowsneak','suckerpunch','vacuumwave','watershuriken', 'jetpunch', 'thunderclap']
momentum = ['uturn','voltswitch','flipturn','partingshot','teleport','batonpass']
stats = ['hp', 'atk', 'def', 'spa', 'spd']
hazards = ['stealthrock', 'spikes', 'toxicspikes', 'stickyweb']
removal = ['rapidspin', 'defog']
cleric = ['wish', 'statusheal']
status_heal = ['healbell','aromatherapy']
immune_abilities = ['Dry Skin', 'Heatproof', 'Fluffy', 'Flash Fire', 'Levitate', "Lightningrod", "Motor Drive", "Sap Sipper", "Storm Drain", "Volt Absorb", "Water Absorb"]
resist_convert = {0: 1, 1: 2, 2:0.5, 3:0}
all_types = [x.lower() for x in typechart.keys() if x.lower() != 'stellar']
col_dict = {4.: '#990000', 2.: "#e06666", 0.: '#434343', 0.5: '#93c47d', 0.25: '#38761d'}
res_to_chartval = {3: 0, 2: 0.25, 1: 0.5, 0: 1, -1: 2, -2: 4, -3: 8}
image_url = "https://www.serebii.net/pokemon/art/"
default_config = {
    "cost_range": (-float('inf'), float('inf')),
    "types": all_types,
    "stealthrock": False,
    'spikes': False,
    'stickyweb': False,
    'toxicspikes': False,
    'rapidspin': False,
    'defog': False,
    'momentum': False,
    'wish': False,
    'statusheal': False,
    'hp': False,
    'atk': False,
    'def': False,
    'spa':False,
    'spd': False,
    "speed_range": (-float('inf'), float('inf'))
}