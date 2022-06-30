import streamlit as st
import py3Dmol
from stmol import showmol
from io import StringIO


def simple_show() -> None:
    pdb_file: StringIO = st.session_state[f'pdb_wild_clean']
    structure = pdb_file.read()
    pdb_file.seek(0)
    view = py3Dmol.view(width=400, height=400)
    view.addModel(structure, 'wild')
    view.setStyle({'stick': {}})
    view.zoomTo()
    showmol(view, height=500, width=800)


def check_files() -> bool:
    constraints = [
        'pdb_wild_clean' in st.session_state.keys(),
        'pdb_variant_clean' in st.session_state.keys()
    ]
    return all(constraints)


def main():
    st.title('Structure View')
    if check_files():
        simple_show()
    else:
        st.error('Not all Requirements are Satisfied')
