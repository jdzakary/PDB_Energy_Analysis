import json
import os
import re
import inspect
import streamlit as st
import pandas as pd
import lib.energy_breakdown as eb
from io import StringIO, BytesIO
from typing import List, Callable
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.ResidueDepth import ResidueDepth
from functools import partial
from threading import Thread
from streamlit.scriptrunner.script_run_context import add_script_run_ctx
from utility import load_text

STATE: dict


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


def new_files() -> None:
    """
    A streamlit callback to refresh file status when new files are uploaded
    :return:
    """
    if 'cleaned' in STATE.keys():
        STATE['cleaned'] = False


def file_uploader(key: str, value: dict) -> None:
    """
    Create the file uploader widget to accept uploaded PDB files
    :param key:
        The file name that will be stored in session state
    :param value:
        A dictionary of arguments for the streamlit widget
    :return:
    """
    STATE[key] = st.file_uploader(**value, on_change=new_files)


def renumber_pdb(file_name: str) -> None:
    """
    Renumber a PDB file so that the first residue is at position 1
    :param file_name:
        The name of the PDB file as stored in streamlit session state
    :return:
    """
    pdb_file = STATE[file_name]
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
    STATE[f'{file_name}_clean'] = result


def fasta(file_name: str) -> List[str]:
    """
    Generate the FASTA sequence of a PDB File
    :param file_name:
        The name of the PDB file as stored in streamlit session state
    :return:
        The FASTA sequence as a list of strings
    """
    parser = PDBParser()
    parser.QUIET = True
    pdb_file = STATE[file_name]
    structure = parser.get_structure(0, pdb_file)
    pdb_file.seek(0)
    return [aa_map[x.resname] for x in structure.get_residues()]


def mutations() -> pd.DataFrame:
    """
    Create the mutations dataframe using files stored in session state
    :return:
        The mutations dataframe
    """
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
    """
    Internal format adjuster for cleaning PDB files
    :param x:
    :return:
    """
    initial = len(x)
    if initial == 1:
        x += '  '
    if initial == 2:
        x += ' '
    if x[0].isnumeric() and initial == 3:
        x += ' '
    return x


def find_start(data: str) -> int:
    """
    Internal format adjuster for cleaning PDB files
    :param data:
    :return:
    """
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
    """
    Clean the PDB files
    :return:
    """
    for i in ['pdb_wild', 'pdb_variant']:
        if STATE[i] is not None:
            renumber_pdb(i)
    STATE['cleaned'] = True
    if 'mut_calc' in STATE.keys():
        STATE['mut_calc'] = False
    if 'depth' in STATE.keys():
        STATE['depth'] = False
    if 'breakdown' in STATE.keys():
        STATE['breakdown'] = False


def find_mutations() -> None:
    """
    Identify the mutations between the wild-type and variant structures
    :return:
    """
    clean = ['pdb_wild_clean', 'pdb_variant_clean']
    if any([x not in STATE.keys() for x in clean]):
        return
    data = mutations()
    STATE['mutations'] = data
    STATE['mut_calc'] = True


def re_upload(key: str) -> None:
    """
    Mark a PDB file for re-upload
    :param key:
        The name of the file as stored in streamlit session state
    :return:
    """
    STATE[key] = None


def calculate_depth(file_name: str) -> None:
    """
    Execute the depth calculations using biopython
    :param file_name:
            A portion of the file name, such as "wild" or "variant", if the
            full name is "pdb_wild_clean" or "pdb_variant_clean"
    :return:
    """
    parser = PDBParser()
    parser.QUIET = True
    pdb_file = STATE[f'pdb_{file_name}_clean']
    structure = parser.get_structure(0, pdb_file)
    pdb_file.seek(0)
    rd = ResidueDepth(
        model=structure[0],
        msms_exec='lib/msms_linux/msms.x86_64Linux2.2.6.1'
    )
    results = {x[1][1]: y[0] for x, y in rd.property_dict.items()}
    STATE[f'depth_{file_name}'] = results
    STATE['depth'] = True


def calculate_energy(file_type: str) -> None:
    """
    Execute the Rosetta Energy Breakdown protocol
    :param file_type:
            A portion of the file name, such as "wild" or "variant", if the
            full name is "pdb_wild_clean" or "pdb_variant_clean"
    :return:
    """
    assert f'pdb_{file_type}_clean' in STATE.keys()
    pdb_file: StringIO = STATE[f'pdb_{file_type}_clean']
    with open(f'lib/storage/{file_type}.pdb', 'w') as file:
        file.write(pdb_file.read())
    pdb_file.seek(0)
    if st.session_state['Home']['rosetta_local']:
        this_dir = os.path.dirname(__file__)
        root = '/'.join(this_dir.split('/')[:-1])
        executable = f'{root}/{st.session_state["Home"]["rosetta_path"]}'
    else:
        executable = st.session_state["Home"]["rosetta_path"]
    print(executable)
    eb.run(
        file_name=f'lib/storage/{file_type}.pdb',
        save_path=f'lib/storage/energy_{file_type}.out',
        log_path=f'lib/storage/log_{file_type}.txt',
        executable=executable
    )
    eb.convert_outfile(
        file_name=f'lib/storage/energy_{file_type}.out',
        save_path=f'lib/storage/energy_{file_type}.csv'
    )
    energy = pd.read_csv(f'lib/storage/energy_{file_type}.csv')
    energy.drop(energy[energy['resi2'] == '--'].index, inplace=True)
    energy['resi2'] = energy['resi2'].astype(int)
    STATE[f'energy_{file_type}'] = energy
    STATE['breakdown'] = True
    os.remove(f'lib/storage/energy_{file_type}.csv')
    os.remove(f'lib/storage/energy_{file_type}.out')


def find_depth(container) -> None:
    """
    Call the calculate_depth function in a separate thread, and monitor
    this thread using add_script_run_ctx
    :return:
    """
    for i in ['wild', 'variant']:
        if f'pdb_{i}_clean' in STATE.keys():
            task = Thread(target=partial(calculate_depth, file_name=i))
            add_script_run_ctx(task)
            task.start()
            container.warning(
                f'Calculations for {i} initiated in separate thread'
            )


def find_energy(container) -> None:
    """
    Call the calculate_energy function in a separate thread, and monitor
    this thread using add_script_run_ctx
    :return:
    """
    for i in ['wild', 'variant']:
        if f'pdb_{i}_clean' in STATE.keys():
            task = Thread(target=partial(calculate_energy, i))
            add_script_run_ctx(task)
            task.start()
            container.warning(
                f'Calculations for {i} initiated in separate thread'
            )


def check_rosetta() -> bool:
    """
    Check if the application has a valid Rosetta Executable to use
    :return:
    """
    if st.session_state['Home']['rosetta_local']:
        return True
    return st.session_state['Home']['rosetta_installed']


def show_action(
    header: str,
    text_file_name: str,
    button_label: str,
    callback: Callable
) -> None:
    """
    Display an action that can be performed on uploaded file data
    :param header:
        The sub-header to name this section
    :param text_file_name:
        The text file identifier on disk to load
    :param button_label:
        The label of the button that will execute the action
    :param callback:
        The action to be executed when the button is pressed
    :return:
    """
    st.subheader(header)
    st.write(load_text('file_upload', text_file_name))
    if text_file_name == 'energy_files' and not check_rosetta():
        st.error('No Rosetta Executable Available!')
        return
    status = st.container()
    status.write('')
    if len(inspect.signature(callback).parameters.keys()):
        st.button(label=button_label, on_click=partial(callback, status))
    else:
        st.button(label=button_label, on_click=callback)


actions = {
    'Cleaning PDB Files': dict(
        text_file_name='pdb_files',
        button_label='Clean PDB Files',
        callback=clean_pdb
    ),
    'Determining Mutations': dict(
        text_file_name='mutations',
        button_label='Find Mutations',
        callback=find_mutations
    ),
    'Residue Depth': dict(
        text_file_name='residue_depth',
        button_label='Calculate Depth',
        callback=find_depth
    ),
    'Rosetta Energy Breakdown Protocol': dict(
        text_file_name='energy_files',
        button_label='Calculate Energy',
        callback=find_energy
    )
}


def use_example(file_name: str) -> None:
    """
    Load an example file from disk and process it appropriately
    :param file_name:
        The file identifier. Either "wild" or "variant"
    :return:
    """
    file = BytesIO()
    with open(f'lib/example_{file_name[4:]}.pdb', 'rb') as stream:
        file.write(stream.read())
    file.seek(0)
    file.name = f'example_{file_name[4:]}.pdb'
    STATE[file_name] = file


def file_uploader_widgets() -> None:
    """
    Create the File Uploaders and the associated functionality, including
    an option to re-upload a file and use an example file.
    :return:
    """
    global KEY
    for key, value in files.items():
        if key not in STATE.keys() or STATE[key] is None:
            file_uploader(key, value)
            st.button(
                label='Use Example File',
                key=KEY,
                on_click=partial(use_example, file_name=key)
            )
            KEY += 1
        else:
            st.success(
                f'{key} is uploaded --- {STATE[key].name}'
            )
            st.button(
                label='Re-upload?',
                key=KEY,
                on_click=partial(re_upload, key=key)
            )
            KEY += 1


def main() -> None:
    """
    Creates the File Upload Page
    :return:
    """
    global STATE
    STATE = st.session_state['File Upload']
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.title('Upload Necessary Data')
        file_uploader_widgets()
        for key, value in actions.items():
            show_action(key, **value)
