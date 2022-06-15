import streamlit as st
from utility import load_text

files = {
    'pdb_wild': {
        'label': 'PDB Structure: Wild-Type',
        'type': ['pdb']
    },
    'pdb_variant': {
        'label': 'PDB Structure: Variant',
        'type': ['pdb']
    },
    'energy_wild': {
        'label': 'Energy Breakdown: Wild-Type',
        'type': ['csv']
    },
    'energy_variant': {
        'label': 'Energy Breakdown Variant',
        'type': ['csv']
    }
}


def file_uploader(
    file_name: str,
    uploader_args: dict
) -> None:
    st.session_state[file_name] = st.file_uploader(**uploader_args)


def main():
    st.title('Upload Necessary Data')

    for key, value in files.items():
        if key not in st.session_state.keys() or st.session_state[key] is None:
            file_uploader(key, value)
        else:
            st.success(f'{value["label"]} --- is already uploaded')

    with st.expander('PDB Files'):
        st.write(load_text('file_upload', 'pdb_files'))
        with open('scripts/clean_pdb.py', 'rb') as file:
            clean_pdb = file.read()
        st.download_button(
            label='PDB Cleaner Script',
            data=clean_pdb,
            file_name='clean_pdb.py',
        )

    with st.expander('Energy Breakdown Files'):
        st.write(load_text('file_upload', 'energy_files'))
        with open('scripts/clean_pdb.py', 'rb') as file:
            energy_breakdown = file.read()
        st.download_button(
            label='Energy Breakdown Script',
            data=energy_breakdown,
            file_name='energy_breakdown.py',
        )

    with st.expander('Residue Depth'):
        st.write(load_text('file_upload', 'residue_depth'))


if __name__ == '__main__':
    main()
