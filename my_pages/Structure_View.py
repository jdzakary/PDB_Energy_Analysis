import streamlit as st
from utility import load_text
from lib.visualization import WebViewer


def parse_resi(user_input: str) -> None:
    state: dict = st.session_state['struct']
    try:
        state['resi'] = [int(x) for x in user_input.split(',')]
    except ValueError:
        st.error('Invalid Residue String')


def create_viewer() -> None:
    state = st.session_state['struct']
    viewer = WebViewer()
    for i in ['wild', 'variant']:
        viewer.add_model(i)
        viewer.show_cartoon(i, state['cartoon'])
        viewer.show_sc(
            i, state['resi'], state[f'{i}_color'], state['cartoon']
        )
    viewer.set_background(state['background'])
    viewer.center('wild', state['resi'])
    viewer.show()


def color_select() -> None:
    state: dict = st.session_state['struct']
    # Background Color
    if 'background' not in state.keys():
        state['background'] = '#E2DFDF'
    color = st.color_picker('Background', state['background'])
    state['background'] = color

    # Cartoon Color
    if 'cartoon' not in state.keys():
        state['cartoon'] = '#858282'
    color = st.color_picker('Cartoon', state['cartoon'])
    state['cartoon'] = color

    # Wild Color
    if 'wild_color' not in state.keys():
        state['wild_color'] = '#04EEF3'
    color = st.color_picker('Wild Color', state['wild_color'])
    state['wild_color'] = color

    # Variant Color
    if 'variant_color' not in state.keys():
        state['variant_color'] = '#0FA81B'
    color = st.color_picker('Variant Color', state['variant_color'])
    state['variant_color'] = color


def tools() -> None:
    state: dict = st.session_state['struct']
    # Residue Selection
    if 'resi' not in state.keys():
        state['resi'] = [1, 2]
    resi = st.text_input(
        label='Show Residue Side Chains:',
        value=','.join([str(x) for x in state['resi']])
    )
    parse_resi(resi)


def check_files() -> bool:
    constraints = [
        'pdb_wild_clean' in st.session_state.keys(),
        'pdb_variant_clean' in st.session_state.keys()
    ]
    return all(constraints)


def main():
    # Create Session State
    if 'struct' not in st.session_state.keys():
        st.session_state['struct'] = {}

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
