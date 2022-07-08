from functools import partial
import streamlit as st
import sys
import os
from PIL import Image
from my_pages import (
    File_Upload, Interaction_Analysis, Residue_Depth, Energy_Heatmap,
    Structure_View, Mutations
)
from utility import load_text
sys.path.append(os.path.dirname(__file__))

STATE: dict
LOCAL_PATH = 'lib/rosetta_linux/source/bin/residue_energy_breakdown' \
             '.static.linuxgccrelease'


def clear_session() -> None:
    """
    Clear the Streamlit Session State
    :return: None
    """
    for key in st.session_state.keys():
        del st.session_state[key]


@st.cache
def load_logo() -> Image:
    """
    Load the Lab Logo to Display in the Sidebar
    :return: Image Object
    """
    logo = Image.open('images/lab_logo.png')
    return logo


def file_status(
    name: str,
    error: str,
    success: str,
    warning: str
) -> None:
    """
    Creates a file status icon in the sidebar
    :param name:
        Name of the file stored in streamlit session state
    :param error:
        Message to display if file is not yet generated
    :param success:
        Message to display if file is up-to-date
    :param warning:
        Message to display if file is outdated
    :return: None
    """
    if name not in st.session_state['File Upload'].keys():
        st.error(error)
    elif st.session_state['File Upload'][name]:
        st.success(success)
    else:
        st.warning(warning)


def ensure_state() -> None:
    """
    Create Session State Dictionaries for Each Page
    :return:
    """
    for i in PAGES.keys():
        if i not in st.session_state.keys():
            st.session_state[i] = {}


def check_local_rosetta() -> None:
    """
    Check if rosetta is included as part of the webserver
    :return:
    """
    exists = os.path.exists(LOCAL_PATH)
    if 'rosetta_installed' not in STATE.keys():
        STATE['rosetta_installed'] = False
        STATE['rosetta_local'] = False
    STATE['rosetta_local'] = exists
    if exists:
        STATE['rosetta_path'] = LOCAL_PATH
        STATE['rosetta_installed'] = True


def check_user_rosetta(path: str) -> bool:
    """
    Validate the user-provided rosetta path
    :param path:
        The user-provided rosetta path
    :return:
    """
    valid_path = os.path.exists(path)
    STATE['rosetta_installed'] = \
        valid_path and 'residue_energy_breakdown' in path
    return valid_path and 'residue_energy_breakdown' in path


def path_input(container) -> None:
    """
    Callback function to dynamically update the status widget without having
    to wait for a page refresh.
    :param container:
        The container to write the status symbol to
    :return:
    """
    STATE['rosetta_path'] = st.session_state['rosetta_path']
    if check_user_rosetta(STATE['rosetta_path']):
        container.success('Successfully Found the Provided Executable')
    else:
        container.error('Unable to find provided filepath')


def detect_rosetta() -> None:
    """
    Ensure that the application knows where to find the Rosetta executable
    :return:
    """
    if STATE['rosetta_local']:
        st.success('Local Rosetta Installation Detected')
    else:
        status = st.container()
        if STATE['rosetta_installed']:
            status.success('Successfully Found the Provided Executable')
        else:
            status.warning('Please Enter the Executable Path')
        st.text_input(
            label='',
            value=STATE['rosetta_path'],
            key='rosetta_path',
            on_change=partial(path_input, status)
        )


def sidebar_title() -> None:
    st.markdown(
        body="<h1 style='text-align: center;'>Kuenze Lab</h1>",
        unsafe_allow_html=True
    )
    logo = load_logo()
    st.image(logo, use_column_width=True)


def home() -> None:
    """
    Creates the Homepage Screen
    :return: None
    """
    left, center, right = st.columns([1, 2, 1])
    check_local_rosetta()
    with center:
        st.title('Energetic Analysis Tools')
        st.header('Introduction')
        st.write(load_text('home', 'introduction'))
        st.subheader('Rosetta Requirement')
        st.write(load_text('home', 'rosetta'))
        if 'rosetta_path' not in STATE.keys():
            STATE['rosetta_path'] = 'main/source/bin/residue_energy_' \
                                    'breakdown.static.linuxgccrelease'
        detect_rosetta()


PAGES = {
    'Home': home,
    'File Upload': File_Upload.main,
    'Interaction Analysis': Interaction_Analysis.main,
    'Residue Depth': Residue_Depth.main,
    'Energy Heatmap': Energy_Heatmap.main,
    'Structure View': Structure_View.main,
    'Mutations': Mutations.main,
}

STATUS = {
    'cleaned': dict(
        error='PDB Files not Cleaned',
        success='PDB Files Cleaned',
        warning='PDB Files Changed, should re-clean'
    ),
    'mut_calc': dict(
        error='Mutations Not Calculated',
        success='Mutations Calculated',
        warning='PDB Files Changed, should re-calculate'
    ),
    'depth': dict(
        error='Residue Depth Not Calculated',
        success='Reside Depth Calculated',
        warning='PDB Files Changed, should re-calculate'
    ),
    'breakdown': dict(
        error='Energy Breakdown Not Calculated',
        success='Energy Breakdown Calculated',
        warning='PDB Files Changed, should re-calculate'
    )
}


def main() -> None:
    """
    Application Entry Point
    :returns: None
    """
    st.set_page_config(
        page_title='Energy Tools',
        page_icon='images/lab_icon.png',
        layout='wide'
    )
    ensure_state()
    global STATE
    STATE = st.session_state['Home']
    with st.sidebar:
        sidebar_title()
        selected = st.selectbox(
            label='Select a Page',
            options=PAGES.keys()
        )
        for key, value in STATUS.items():
            file_status(name=key, **value)
    PAGES[selected]()


if __name__ == '__main__':
    os.environ["NUMEXPR_MAX_THREADS"] = '8'
    main()
