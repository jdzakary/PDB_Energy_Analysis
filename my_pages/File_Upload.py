import json
import os
import re
import streamlit as st
import pandas as pd
import lib.energy_breakdown as eb
from io import StringIO
from typing import List
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.ResidueDepth import ResidueDepth
from functools import partial
from threading import Thread
from streamlit.scriptrunner.script_run_context import add_script_run_ctx
from utility import load_text

with open('lib/aa_map.json', 'r') as my_file:
    aa_map = json.load(my_file)

files = {
    'pdb_wild': {
        'label': 'PDB Structure: Wild-Type',
        'type': ['pdb'],
    },
    'pdb_variant': {
        'label': 'PDB Structure: Variant',
        'type': ['pdb'],
    }
}

KEY = 1


def new_files():
    if 'cleaned' in st.session_state.keys():
        st.session_state['cleaned'] = False


def file_uploader(key: str, value: dict) -> None:
    st.session_state[key] = st.file_uploader(**value, on_change=new_files)


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


def fasta(file_name: str) -> List[str]:
    parser = PDBParser()
    parser.QUIET = True
    pdb_file = st.session_state[file_name]
    structure = parser.get_structure(0, pdb_file)
    pdb_file.seek(0)
    return [aa_map[x.resname] for x in structure.get_residues()]


def mutations() -> pd.DataFrame:
    variant = fasta('pdb_variant_clean')
    wild = fasta('pdb_wild_clean')
    assert len(variant) == len(wild)
    counter = 1
    results = []
    for v, w in zip(variant, wild):
        if v != w:
            results.append([counter, v, w])
        counter += 1
    results = pd.DataFrame(results)
    results.columns = ['Position', 'Mutated', 'Wild']
    results.sort_values(by='Position', inplace=True)
    results.set_index(keys='Position', inplace=True)
    return results


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
    for i in ['pdb_wild', 'pdb_variant']:
        if st.session_state[i] is not None:
            renumber_pdb(i)
    st.session_state['cleaned'] = True
    if 'mut_calc' in st.session_state.keys():
        st.session_state['mut_calc'] = False
    if 'depth' in st.session_state.keys():
        st.session_state['depth'] = False
    if 'breakdown' in st.session_state.keys():
        st.session_state['breakdown'] = False


def find_mutations() -> None:
    clean = ['pdb_wild_clean', 'pdb_variant_clean']
    if any([x not in st.session_state.keys() for x in clean]):
        return
    data = mutations()
    st.session_state['mutations'] = data
    st.session_state['mut_calc'] = True


def re_upload(key: str):
    st.session_state[key] = None


def calculate_depth(file_name: str) -> None:
    parser = PDBParser()
    parser.QUIET = True
    pdb_file = st.session_state[f'pdb_{file_name}_clean']
    structure = parser.get_structure(0, pdb_file)
    pdb_file.seek(0)
    rd = ResidueDepth(
        model=structure[0],
        msms_exec='lib/msms_linux/msms.x86_64Linux2.2.6.1'
    )
    results = {x[1][1]: y[0] for x, y in rd.property_dict.items()}
    st.session_state[f'depth_{file_name}'] = results
    print(f'Finished with {file_name}')


def calculate_energy(file_type: str) -> None:
    assert f'pdb_{file_type}_clean' in st.session_state.keys()
    pdb_file: StringIO = st.session_state[f'pdb_{file_type}_clean']
    with open(f'lib/storage/{file_type}.pdb', 'w') as file:
        file.write(pdb_file.read())
    pdb_file.seek(0)
    eb.run(
        file_name=f'lib/storage/{file_type}.pdb',
        save_path=f'lib/storage/energy_{file_type}.out',
        log_path=f'lib/storage/log_{file_type}.txt'
    )
    eb.convert_outfile(
        file_name=f'lib/storage/energy_{file_type}.out',
        save_path=f'lib/storage/energy_{file_type}.csv'
    )
    energy = pd.read_csv(f'lib/storage/energy_{file_type}.csv')
    energy.drop(energy[energy['resi2'] == '--'].index, inplace=True)
    energy['resi2'] = energy['resi2'].astype(int)
    st.session_state[f'energy_{file_type}'] = energy
    os.remove(f'lib/storage/energy_{file_type}.csv')
    os.remove(f'lib/storage/energy_{file_type}.out')


def find_depth():
    for i in ['wild', 'variant']:
        if f'pdb_{i}_clean' in st.session_state.keys():
            st.session_state['depth'] = True
            task = Thread(target=partial(calculate_depth, file_name=i))
            add_script_run_ctx(task)
            task.start()


def find_energy():
    for i in ['wild', 'variant']:
        if f'pdb_{i}_clean' in st.session_state.keys():
            st.session_state['breakdown'] = True
            task = Thread(target=partial(calculate_energy, i))
            add_script_run_ctx(task)
            task.start()


def main():
    left, center, right = st.columns([1, 2, 1])
    global KEY
    with center:
        st.title('Upload Necessary Data')
        for key, value in files.items():
            if key not in st.session_state.keys() or st.session_state[key] is None:
                file_uploader(key, value)
            else:
                st.success(
                    f'{key} is uploaded --- {st.session_state[key].name}'
                )
                st.button(
                    label='Re-upload?',
                    key=KEY,
                    on_click=partial(re_upload, key=key)
                )
                KEY += 1

        st.subheader('Cleaning PDB Files')
        st.write(load_text('file_upload', 'pdb_files'))
        st.button(label='Clean PDB Files', on_click=clean_pdb)

        st.subheader('Determining Mutations')
        st.write(load_text('file_upload', 'mutations'))
        st.button(label='Find Mutations', on_click=find_mutations)

        st.subheader('Residue Depth')
        st.write(load_text('file_upload', 'residue_depth'))
        st.button(label='Calculate Depth', on_click=find_depth)

        st.subheader('Rosetta Energy Breakdown Protocol')
        st.write(load_text('file_upload', 'energy_files'))
        st.button(label='Calculate Energy', on_click=find_energy)
