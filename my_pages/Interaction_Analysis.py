import json
import pandas as pd
import streamlit as st
from utility import load_text
from lib.energy_breakdown import energy_calc
from st_aggrid import (
    AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder
)

STATE: dict

KEY = 1
categories = {
    'salt_changes': 'Salt Bridges',
    'sulfide_changes': 'Sulfide Bonds',
    'hbonds_sc_sc': 'Hydrogen Bonds: Side-Chain to Side-Chain',
    'hbonds_bb_sc': 'Hydrogen Bonds: Side-Chain to Backbone',
    'hbonds_bb_bb_sr': 'Hydrogen Bonds: Backbone to Backbone Short Range',
    'hbonds_bb_bb_lr': 'Hydrogen Bonds: Backbone to Backbone Long Range',
    'all_changes': 'All Interactions'
}


def change_types() -> None:
    """
    Display information explaining the 6 categories of changes
    :return:
    """
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
    """
    Check that the required files exist in session state
    :return:
    """
    constraints = [
        'energy_wild' in st.session_state['File Upload'].keys(),
        'energy_variant' in st.session_state['File Upload'].keys(),
        'mutations' in st.session_state['File Upload'].keys()
    ]
    return all(constraints)


# TODO: Put this in a separate thread to prevent GUI Freeze
def start_calculations(progress_bar) -> None:
    """
    Execute the interaction analysis
    :param progress_bar:
    :return:
    """
    STATE['results'] = energy_calc(
        variant=st.session_state['File Upload']['energy_variant'],
        wild_type=st.session_state['File Upload']['energy_wild'],
        mutations=st.session_state['File Upload']['mutations'],
        bar=progress_bar
    )
    STATE['complete'] = True


def build_options(data: pd.DataFrame) -> dict:
    """
    Configure options for the AgGrid Widget
    :param data:
    :return:
    """
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_default_column(resizable=False)
    gb.configure_pagination(
        paginationAutoPageSize=False,
        paginationPageSize=30
    )
    gb.configure_column(
        field='Resi2',
        menuTabs=['generalMenuTab', 'filterMenuTab']
    )
    options = gb.build()
    return options


def display_changes(label: str) -> None:
    """
    Display the results in an AgGrid Widget
    :param label:
    :return:
    """
    data = []
    for key, df in STATE['results'][label].items():
        if len(df) > 0:
            df: pd.DataFrame
            new = df[['resi1', 'resi2', 'total']].values.tolist()
            new = [x + [key.upper()] for x in new]
            data.extend(new)
    data = pd.DataFrame(data)
    data.columns = ['Resi1', 'Resi2', 'Total', 'Change Type']
    data['Total'] = data['Total'].round(3)
    data.insert(0, 'Change Type', data.pop('Change Type'))
    options = build_options(data)
    grid_response = AgGrid(
        dataframe=data,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.NO_UPDATE,
        gridOptions=options,
        try_to_convert_back_to_original_types=False,
        theme='streamlit'
    )


def main():
    """
    Create the Interaction Analysis Main Page
    :return:
    """
    global STATE
    STATE = st.session_state['Interaction Analysis']
    left, center, right = st.columns([1, 2, 1])
    with center:
        if 'complete' not in STATE.keys():
            STATE['complete'] = False
        if 'check' not in STATE.keys():
            STATE['check'] = {
                x: {
                    y: False for y in ['a', 'b', 'c', 'd', 'e', 'f']
                } for x in categories.keys()
            }

        st.title('Changes in Pairwise Interactions')

        st.header('Introduction')
        st.write(load_text('interaction_changes', 'introduction'))
        change_types()

        st.header('Execute the Analysis')
        if not check_files():
            st.error('Error: Not all Pre-requisites are calculated')
            return
        st.success('Checking Pre-requisites: Success!')

        container = st.container()
        analysis_bar = st.progress(100 if STATE['complete'] else 0)
        container.button(
            label='Start Calculations',
            on_click=lambda: start_calculations(analysis_bar),
            disabled=STATE['complete']
        )
        if not STATE['complete']:
            return
        st.success('Successfully Executed Analysis and Stored the Results')

        st.header('Results')
        with st.expander('Summary', expanded=True):
            st.table(STATE['results']['summary'])
        for key, value in categories.items():
            with st.expander(value):
                display_changes(key)
