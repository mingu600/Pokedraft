from data import default_config, image_url, col_dict, all_types
from utils import preprocess_name, _create_total_df, _evaluate_resists, _create_group_df, _name_to_mon, restrictions, _calculate_best_mons, _gsheets, get_image, path_to_image_html, _create_chart, change_color, _create_team_chart
import pandas as pd
import streamlit as st
from tweaker import st_tweaker

st.set_page_config(layout="wide", page_title ='PokéDraft', page_icon = 'spheal-modified.png')

@st.cache_resource
def create_group_df(total_df, num_mons):
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

@st.cache_data(ttl="60s")
def gsheets(base, sheet, header=False):
    if header:
        return pd.read_csv(_gsheets(base, sheet))
    return pd.read_csv(_gsheets(base, sheet), header=None)

@st.cache_data
def create_chart(curr_team, total_df):
    return _create_chart(curr_team, total_df)

@st.cache_data
def create_team_chart(curr_team, total_df):
    return _create_team_chart(curr_team, total_df)

def main():
    title_cols = st.columns([0.01, 0.12, 0.5, 0.8 ])
    title_cols[1].image('spheal-modified.png', width=100)
    title_cols[2].title('PokéDraft')
    tab1, tab2, tab3, tab4 = st.tabs(["Calculate best candidate Pokémon to draft", "What is PokéDraft?", "Google Sheets Format", "About me / Report a bug"])
    
    with tab2:
        st.header("How to use")
        st.write("PokéDraft is a tool intended to help you draft a Pokémon in a standard points-style draft format.")
        st.write("It operates by receiving the tierings, your current team, the Pokémon out of the pool, and your desirable goals to select the best Pokémon that you should draft next.")
        st.write("You can select whether you want to consider 1 or 2 candidate Pokémon at a time.")
        st.subheader("Necessary Constraints")
        st.write("Necessary constraints are requirements that must be satisfied by any suggested groups.") 
        st.write("For example, checking Stealth Rock under hazard setting restrictions means that, if # of Pokémon is set to 2, at least 1 of them has to learn Stealth Rock.")
        st.write("If # of Pokémon is set to 1, then the one suggested Pokémon MUST learn Stealth Rock.")
        st.write("For typing constraints, at least one of the Pokémon must be of one of the types you provide. For stat restrictions, at least one of the Pokémon need to have that stat>=110 (the bound for HP is 90).")
        st.write("The more necessary constraints you add, the faster a solution is found, because you are filtering the entire pool of Pokémon smaller and smaller.")
        st.subheader("Useful Conditions")
        st.write("Useful conditions are extra conditions that are nice to have, but not required. These are the conditions that will lead to the score reported by the tool, as a way of differentiating between possibilities.")
        st.write("They are just as important as necessary conditions- otherwise, it'd be impossible to tell which group of Pokémon is better if they satisfy the necessary requirements.")
        st.write("I suggest always turning on the team type weakness condition- it uses almost the same overall scoring highlighted by the BaLLHaWK prep doc and is showcased by the bottom total row of 'Team type weakness chart'.")
        st.write("Each one of these conditions can be weighted for how much it should contribute to the overall score when evaluating options.")

    with tab3:
        st.header("Google Sheets Format")
        st.write("Here is an example of what PokéDraft expects: https://docs.google.com/spreadsheets/d/1xCcVPFrUA3C_wMm3e3SKj0p2pCOp_8RVPzpPQxzeHMg/edit#gid=1562113146")
        st.write("Remember to set sharing options to allow anyone with link to view.")
        st.write("The doc must have 3 sheets with these exact names: MyTeam, OthersDrafted, and Tiers. For MyTeam and OthersDrafted, list the relevant Pokemon as a single column.")
        st.write("For the Tiers sheet, make sure to take note of how the tiers are formatted and copy it exactly (with the max cost as the first column, all the costs as the first row headers, etc).")
        st.write("Also keep note of how all the Pokemon names are written, including alternate forms, megas, etc. These have to be consistent for PokéDraft to work.")

    with tab4:
        st.header("About Me / Report a bug")
        st.write("Hello! My name is Mingu, and I've been playing Pokemon draft leagues for many years. Lately, I've been playing in fewer leagues, but I've always been interested in applying my tech experience to Pokemon.")
        st.write("I'm in the machine learning/data science space, but this is my first publicly deployed app, so please be understanding if there are any major bugs...")
        st.write("If you find any bugs, feel free to add and message me on Discord (mingu600)!")

    with tab1:
        cost_dict = {}
        curr_team = []
        others_drafted = []
        link = st.text_input("Google Sheets URL (see 'Google Sheets Format' tab for details)")
        try:
            base = link[link.find('/d/') + 3: link.find('/edit')]
            curr_team = gsheets(base, 'MyTeam').values
            others_drafted = gsheets(base, 'OthersDrafted').values

            costs = gsheets(base, 'Tiers', header=True).T
            for index, row in costs.iterrows():
                for mon in row.dropna():
                    cost_dict[preprocess_name(mon)] = int(index)

        except:
            st.write(":red[URL or Google Sheets format incorrect. Please refer to 'Google Sheets Format' for instructions]")
            st.stop()

        total_df = create_total_df(cost_dict)
        name_map = name_to_mon(total_df)

        curr_team = [name_map[x[0]] for x in curr_team]
        others_drafted = [name_map[x[0]] for x in others_drafted]

        sprites, speeds, normal, fire, water, electric, grass, ice, fighting, poison, ground, flying, psychic, bug, rock, ghost, dragon , dark, steel, fairy = create_chart(curr_team, total_df)
        typechart_df = pd.DataFrame({'Pokémon': sprites, 'Speed': speeds, 'Normal': normal, 'Fire': fire, 'Water': water, 'Electric': electric, 'Grass': grass, 'Ice': ice,
                                        'Fighting': fighting, 'Poison': poison, 'Ground': ground, 'Flying': flying, 'Psychic': psychic, 'Bug': bug, 'Rock': rock,
                                        'Ghost': ghost, 'Dragon': dragon, 'Dark': dark, 'Steel': steel, 'Fairy': fairy})

        sprites, ability1, ability2, ability3, stealthrock, spikes, toxicspikes, stickyweb, defog, rapidspin, wish, statusheal, momentum, priority = create_team_chart(curr_team, total_df)
        teamchart_df = pd.DataFrame({'Pokémon': sprites, 'Ability 1': ability1, 'Ability 2': ability2, 'Ability 3': ability3, 'Stealth Rock':stealthrock, 'Spikes': spikes, 'Toxic Spikes': toxicspikes,
                                     'Sticky Web': stickyweb, 'Defog': defog, 'Rapid Spin': rapidspin, 'Wish': wish, 'Status Heal': statusheal, 'Momentum': momentum, 'Priority': priority})

        team_expander = st.expander("Team info")
        with team_expander:
            st.markdown(
                change_color(teamchart_df.to_html(escape=False, formatters=dict(Pokémon=path_to_image_html), index=False)),
                unsafe_allow_html=True,
            )      

        typechart_expander = st.expander("Team type weakness chart")
        with typechart_expander:
            st.markdown(
                change_color(typechart_df.to_html(escape=False, formatters=dict(Pokémon=path_to_image_html), index=False)),
                unsafe_allow_html=True,
            )

        #col1, dummy, col2, col3 = st.columns([1, 0.25, 1, 1])
        dummy1, col1, dummy, col2, col3 = st_tweaker.columns(spec = [0.01, 1.5, 0.25, 1, 1], id = "main_cols",css = "#main_cols {overflow: auto; height: 70vh;}")

        num_mons = col1.radio("Number of candidate Pokémon to evaluate", [1, 2], horizontal=True)
        necessary_config = {}
        useful_config = {}
        necessary_config = restrictions(True, total_df, necessary_config, col1, num_mons)
        useful_config = restrictions(False, total_df, useful_config, col1, num_mons, necessary_config)




        config = default_config.copy()
        for p in necessary_config:
            config[p] = necessary_config[p]
        group_df = create_group_df(total_df, num_mons)
        next_df = group_df.copy()
        col4, col5 = col1.columns([1, 1])
        calc_button = col4.button("Calculate best candidate Pokémon", type="primary")
        cancel_button = col5.button("Cancel")
        if calc_button:
            if cancel_button:
                col4.subheader(":red[Calculation cancelled. Please edit restrictions and try again.]")
                st.stop()
            with st.spinner('Calculating...'):
                result = calculate_best_mons(next_df, config, useful_config, total_df, curr_team, others_drafted, keep_n=10)
            if not result:
                col1.subheader(":red[No results. Please edit restrictions and try again.]")
            else:
                col1.success('Done!')
            for i, (score, group) in enumerate(result):
                names, images = get_image(group, total_df)
                if i % 2 == 0:
                    col2.subheader("Score: " + str(round(float(score), 3)))
                    col2.image(images, caption=names, width=200)
                else:
                    col3.subheader("Score: " + str(round(float(score), 3)))
                    col3.image(images, caption=names, width=200)                   

    

if __name__ == "__main__":
    main()