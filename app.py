from data import default_config, image_url
from utils import preprocess_name, _create_total_df, _evaluate_resists, _create_group_df, _name_to_mon, restrictions, _calculate_best_mons
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_resource
def create_group_df(total_df, num_mons):
    print(num_mons)
    return _create_group_df(total_df, num_mons)

@st.cache_data
def name_to_mon(total_df):
    return _name_to_mon(total_df)

@st.cache_data
def evaluate_resists(total_df, team):
    return _evaluate_resists(total_df, team)

@st.cache_resource
def create_total_df(cost_dict):
    return _create_total_df(cost_dict)

@st.cache_data(show_spinner=False)
def calculate_best_mons(next_df, config, useful_config, total_df, curr_team, others_drafted, keep_n=10):
    return _calculate_best_mons(next_df, config, useful_config, total_df, curr_team, others_drafted, keep_n=10)

def main():
    st.title('PokéDraft')

    st.header('Upload costs for Pokémon as a csv file')
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        costs = pd.read_csv(uploaded_file).T
        cost_dict = {}
        for index, row in costs.iterrows():
            for mon in row.dropna():
                cost_dict[preprocess_name(mon)] = int(index)

        total_df = create_total_df(cost_dict)

        name_map = name_to_mon(total_df)
        all_mon_names = total_df['name']

        curr_team = st.multiselect(label='Select current team members (Pokémon you have already drafted)', options=all_mon_names, default=[])
        curr_team = [name_map[x] for x in curr_team]

        others_drafted = st.multiselect(label='Select Pokémon that other people have drafted (excluding your own)', options=all_mon_names, default=[])
        others_drafted = [name_map[x] for x in others_drafted]

        num_mons = st.radio("Number of candidate Pokémon to evaluate", [1, 2])

        necessary_config = {}
        useful_config = {}

        necessary_config = restrictions(True, total_df, necessary_config)
        useful_config = restrictions(False, total_df, useful_config, necessary_config)

        config = default_config.copy()
        for p in necessary_config:
            config[p] = necessary_config[p]
        group_df = create_group_df(total_df, num_mons)
        next_df = group_df.copy()
        if st.button("Calculate best candidate Pokémon to draft", type="primary"):
            with st.spinner('Calculating...'):
                result = calculate_best_mons(next_df, config, useful_config, total_df, curr_team, others_drafted, keep_n=10)
            if not result:
                st.subheader(":red[No results. Please edit restrictions and try again.]")
            else:
                st.success('Done!')
                for score, group in result:
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
                        images.append(image_url + str(total_df.loc[mon]['num']).zfill(3) +  im_tag)
                    st.subheader("Score: " + str(round(float(score), 3)))
                    st.image(images, caption=names, width=200)

if __name__ == "__main__":
    main()