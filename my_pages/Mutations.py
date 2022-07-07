import pandas as pd
import streamlit as st
from st_aggrid import (
    AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder
)

STATE: dict


def check_files() -> bool:
    """
    Check that necessary files are stored in session state
    :return:
    """
    constraints = [
        'mutations' in st.session_state['File Upload'].keys()
    ]
    return all(constraints)


def adjust_mutations() -> pd.DataFrame:
    """
    Adjust the mutations dataframe stored in session state
    :return:
    """
    data: pd.DataFrame = st.session_state['File Upload']['mutations']
    new = data.reset_index(0)
    return new


def build_options(data: pd.DataFrame) -> dict:
    """
    Configure options for AgGrid
    :param data:
    :return:
    """
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_default_column(
        resizable=False
    )
    gb.configure_selection(
        selection_mode='multiple',
        use_checkbox=True
    )
    options = gb.build()
    return options


def show_grid():
    """
    Show the mutations in AgGrid
    :return:
    """
    data = adjust_mutations()
    options = build_options(data)
    grid_response = AgGrid(
        dataframe=data,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        gridOptions=options,
        try_to_convert_back_to_original_types=False
    )
    selected = grid_response['selected_rows']
    selected_df = pd.DataFrame(selected)
    st.write(selected_df)


def main():
    """
    Create the Mutations Main Page
    :return:
    """
    global STATE
    STATE = st.session_state['Mutations']
    columns = st.columns([1, 3, 1])
    with columns[1]:
        st.title('Check Mutations')
        if check_files():
            show_grid()
        else:
            st.error('Not all Pre-Requisites are Calculated')
