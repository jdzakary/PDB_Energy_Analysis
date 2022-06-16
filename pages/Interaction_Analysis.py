import json
import pandas as pd
import streamlit as st
from utility import load_text
from lib.energy_breakdown import energy_calc, load_interactions

KEY = 1


def change_types() -> None:
    data = pd.DataFrame([
        ['A', True, True, False],
        ['B', True, True, True],
        ['C', True, False, False],
        ['D', True, False, True],
        ['E', False, True, False],
        ['F', False, True, True]
    ])
    data.columns = [
        'Type of Change',
        'Positions Interacting in Wild-Type',
        'Positions Interacting in Variant',
        'Involving Mutated Residues'
    ]
    data.set_index('Type of Change', inplace=True)
    st.table(data)
    with open(f'text/interaction_changes/changes.json', 'r') as file:
        descriptions = json.load(file)
    data_2 = pd.DataFrame(descriptions['data'])
    data_2.columns = ['Change Type', 'Description']
    data_2.set_index('Change Type', inplace=True)
    data_2.columns = ['Description']
    st.table(data_2)


def check_files() -> bool:
    files = ['energy_wild', 'energy_variant', 'mutations']
    if any([x not in st.session_state.keys() for x in files]):
        return False
    return all([st.session_state[x] is not None for x in files])


def start_calculations(progress_bar) -> None:
    files = load_interactions(
        energy_variant=st.session_state['energy_variant'],
        energy_wild=st.session_state['energy_wild'],
        mutations=st.session_state['mutations']
    )
    st.session_state['results'] = energy_calc(**files, bar=progress_bar)
    st.session_state['complete'] = True


def display_changes(label: str) -> None:
    global KEY
    columns = st.columns(
        sum([len(x) > 0 for x in st.session_state['results'][label]])
    )
    i = 0
    for key, value in st.session_state['results'][label].items():
        if len(value):
            if columns[i].checkbox(f'Type {key.upper()}', key=KEY):
                st.write(f'Changes of Type {key.upper()}')
                st.table(value[['resi1', 'resi2', 'total']])
            i += 1
            KEY += 1


def main():
    if 'complete' not in st.session_state.keys():
        st.session_state['complete'] = False

    st.title('Changes in Pairwise Interactions')

    st.header('Introduction')
    st.write(load_text('interaction_changes', 'introduction'))
    change_types()

    st.header('Execute the Analysis')
    if not check_files():
        st.error('Error: Not all required files are Uploaded!')
        return
    st.success('Checking Uploaded Files: Success')

    container = st.container()
    analysis_bar = st.progress(100 if st.session_state['complete'] else 0)
    container.button(
        label='Start Calculations',
        on_click=lambda: start_calculations(analysis_bar),
        disabled=st.session_state['complete']
    )
    if not st.session_state['complete']:
        return
    st.success('Successfully Executed Analysis and Stored the Results')

    st.header('Results')
    with st.expander('Summary', expanded=True):
        st.table(st.session_state['results']['summary'])
    with st.expander('Salt Bridges'):
        display_changes('salt_changes')
    with st.expander('Sulfide Bonds'):
        display_changes('sulfide_changes')
    with st.expander('Hydrogen Bonds: Side-Chain to Side-Chain'):
        display_changes('hbonds_sc_sc')
    with st.expander('Hydrogen Bonds: Side-Chain to Backbone'):
        display_changes('hbonds_bb_sc')
    with st.expander('Hydrogen Bonds: Backbone to Backbone Short Range'):
        display_changes('hbonds_bb_bb_sr')
    with st.expander('Hydrogen Bonds: Backbone to Backbone Long Range'):
        display_changes('hbonds_bb_bb_lr')


if __name__ == '__main__':
    main()
