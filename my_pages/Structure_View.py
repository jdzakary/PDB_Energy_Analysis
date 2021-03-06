import streamlit as st
from utility import load_text
from lib.visualization import WebViewer

STATE: dict


def parse_resi(user_input: str) -> None:
    """
    Read the residue selection string
    :param user_input:
    :return:
    """
    try:
        STATE['resi'] = [int(x) for x in user_input.split(',')]
    except ValueError:
        st.error('Invalid Residue String')


def create_viewer() -> None:
    """
    Create the PDB structure viewer
    :return:
    """
    viewer = WebViewer()
    for i in ['wild', 'variant']:
        viewer.add_model(i)
        viewer.show_cartoon(i, STATE['cartoon'])
        viewer.show_sc(
            i, STATE['resi'], STATE[f'{i}_color'], STATE['cartoon']
        )
    viewer.set_background(STATE['background'])
    viewer.center('wild', STATE['resi'])
    viewer.show()


def color_select() -> None:
    """
    Create color pickers for changing colors
    :return:
    """
    # Background Color
    if 'background' not in STATE.keys():
        STATE['background'] = '#E2DFDF'
    color = st.color_picker('Background', STATE['background'])
    STATE['background'] = color

    # Cartoon Color
    if 'cartoon' not in STATE.keys():
        STATE['cartoon'] = '#858282'
    color = st.color_picker('Cartoon', STATE['cartoon'])
    STATE['cartoon'] = color

    # Wild Color
    if 'wild_color' not in STATE.keys():
        STATE['wild_color'] = '#04EEF3'
    color = st.color_picker('Wild Color', STATE['wild_color'])
    STATE['wild_color'] = color

    # Variant Color
    if 'variant_color' not in STATE.keys():
        STATE['variant_color'] = '#0FA81B'
    color = st.color_picker('Variant Color', STATE['variant_color'])
    STATE['variant_color'] = color


def tools() -> None:
    """
    Create toolbar for selecting residues
    :return:
    """
    # Residue Selection
    if 'resi' not in STATE.keys():
        STATE['resi'] = [1, 2]
    resi = st.text_input(
        label='Show Residue Side Chains:',
        value=','.join([str(x) for x in STATE['resi']])
    )
    parse_resi(resi)


def check_files() -> bool:
    """
    Check that necessary files exist in session state
    :return:
    """
    constraints = [
        'pdb_wild_clean' in st.session_state['File Upload'].keys(),
        'pdb_variant_clean' in st.session_state['File Upload'].keys()
    ]
    return all(constraints)


def main():
    """
    Create the Structure View Main Page
    :return:
    """
    global STATE
    STATE = st.session_state['Structure View']
    st.title('Structure View')
    st.info(load_text('structure_view', 'align_warning'))
    if check_files():
        columns = st.columns([8, 1, 5])
        with columns[1]:
            color_select()
        with columns[2]:
            tools()
        with columns[0]:
            create_viewer()
    else:
        st.error('Not all Requirements are Satisfied')
