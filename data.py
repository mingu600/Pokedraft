import json

with open('learnsets.json', 'r') as f:
  learnsets = json.load(f)
with open('pokedex.json', 'r', encoding="utf8") as f:
  pokedex = json.load(f)
with open('typechart.json', 'r') as f:
  typechart = json.load(f)

priority_moves = ['accelerock', 'aquajet','bulletpunch','extremespeed','fakeout','firstimpression','iceshard','machpunch','quickattack',
'shadowsneak','suckerpunch','vacuumwave','watershuriken']
momentum = ['uturn','voltswitch','flipturn','partingshot','teleport','batonpass']
status_heal = ['healbell','aromatherapy']
immune_abilities = ['Dry Skin', 'Heatproof', 'Fluffy', 'Flash Fire', 'Levitate', "Lightningrod", "Motor Drive", "Sap Sipper", "Storm Drain", "Volt Absorb", "Water Absorb"]
resist_convert = {0: 1, 1: 2, 2:0.5, 3:0}
all_types = [x.lower() for x in typechart.keys() if x.lower() != 'stellar']

image_url = "https://www.serebii.net/pokemon/art/"
default_config = {
    "cost_range": (1, 18),
    "types": [],
    "rocks": False,
    "speed_range": (-float('inf'), float('inf'))
}