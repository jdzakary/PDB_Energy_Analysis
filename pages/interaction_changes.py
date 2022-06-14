import json
import pandas as pd
import streamlit as st
from utility import load_text


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
    files = ['energy_wild', 'energy_variant']
    if any([x not in st.session_state.keys() for x in files]):
        return False
    return all([st.session_state[x] is not None for x in files])


def main():
    st.title('Changes in Pairwise Interactions')
    st.header('Introduction')
    st.write(load_text('interaction_changes', 'introduction'))
    change_types()
    st.header('Execute the Analysis')
    if check_files():
        st.success('Checking Uploaded Files: Success')
    else:
        st.error('Error: Not all required files are Uploaded!')


if __name__ == '__main__':
    main()
