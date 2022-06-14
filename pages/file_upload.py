import streamlit as st

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


if __name__ == '__main__':
    main()
