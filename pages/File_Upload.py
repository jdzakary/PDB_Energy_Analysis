import streamlit as st
from io import StringIO
import pandas as pd
import re

files = {
    'pdb_wild': {
        'label': 'PDB Structure: Wild-Type',
        'type': ['pdb'],
    },
    'pdb_variant': {
        'label': 'PDB Structure: Variant',
        'type': ['pdb'],
    },
    'energy_wild': {
        'label': 'Energy Breakdown: Wild-Type',
        'type': ['csv']
    },
    'energy_variant': {
        'label': 'Energy Breakdown: Variant',
        'type': ['csv']
    },
    'mutations': {
        'label': 'Mutations Files',
        'type': ['csv']
    }
}


def file_uploader(key: str, value: dict) -> None:
    st.session_state[key] = st.file_uploader(**value)


def renumber_pdb(file_name: str) -> None:
    pdb_file = st.session_state[file_name]
    temp_file = StringIO()
    raw = pdb_file.read()
    text = raw.decode('utf-8').split('\n')
    rows = [x for x in text if x[0:4] == 'ATOM']
    offset = 1 - find_start(rows[0])
    temp_file.write('\n'.join(rows))
    temp_file.seek(0)
    data = pd.read_fwf(temp_file, header=None, infer_nrows=2000)

    data.columns = [
        'ATOM', 'atom_number', 'PDB_atom', 'resi_3', 'resi_1',
        'resi_number', 'A', 'B', 'C', 'D', 'E', 'atom'
    ]
    data['resi_number'] = data['resi_number'] + offset
    data['PDB_atom'] = data['PDB_atom'].apply(adjust_pdb)
    rows = []
    spacing = [4, 7, 5, 4, 2, 4, 12, 8, 8, 6, 6, 12]
    for row in data.iterrows():
        row_txt = ""
        counter = 0
        for column in row[1].values.tolist():
            row_txt += f'{column:>{spacing[counter]}}'
            counter += 1
        rows.append(row_txt)

    result = StringIO()
    result.write('\n'.join(rows))
    result.seek(0)
    pdb_file.seek(0)
    st.session_state[f'{file_name}_clean'] = result


def adjust_pdb(x: str) -> str:
    initial = len(x)
    if initial == 1:
        x += '  '
    if initial == 2:
        x += ' '
    if x[0].isnumeric() and initial == 3:
        x += ' '
    return x


def find_start(data: str) -> int:
    start = data.find(re.findall(r'\w\w\w \w', data)[0]) + 5
    number = ''
    final = False
    while len(number) == 0 or not final:
        if data[start].isnumeric():
            number += data[start]
        elif len(number) > 0:
            final = True
        start += 1
    return int(number)


def clean_pdb() -> None:
    for file in ['pdb_wild', 'pdb_variant']:
        if st.session_state[file] is not None:
            renumber_pdb(file)


def main():
    st.title('Upload Necessary Data')

    for key, value in files.items():
        if key not in st.session_state.keys() or st.session_state[key] is None:
            file_uploader(key, value)
        else:
            st.success(f'{key} is uploaded --- {st.session_state[key].name}')

    st.button(
        label='Clean PDB Files',
        on_click=clean_pdb
    )


if __name__ == '__main__':
    main()
