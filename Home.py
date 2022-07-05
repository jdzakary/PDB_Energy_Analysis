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


def home() -> None:
    """
    Creates the Homepage Screen
    :return: None
    """
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.title('Energetic Analysis Tools')
        st.header('Introduction')
        st.write(load_text('home', 'introduction'))
        st.header('Reset the Application')
        st.error('Warning! This will Clear all Data!')
        st.button('Reset', on_click=clear_session)


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
    if name not in st.session_state.keys():
        st.error(error)
    elif st.session_state[name]:
        st.success(success)
    else:
        st.warning(warning)


pages = {
    'Home': home,
    'File Upload': File_Upload.main,
    'Interaction Analysis': Interaction_Analysis.main,
    'Residue Depth': Residue_Depth.main,
    'Energy Heatmap': Energy_Heatmap.main,
    'Structure View': Structure_View.main,
    'Mutations': Mutations.main,
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
    with st.sidebar:
        st.markdown(
            body="<h1 style='text-align: center;'>Kuenze Lab</h1>",
            unsafe_allow_html=True
        )
        logo = load_logo()
        st.image(logo, use_column_width=True)
        selected = st.selectbox(
            label='Select a Page',
            options=pages.keys()
        )
        file_status(
            name='cleaned',
            error='PDB Files not Cleaned',
            success='PDB Files Cleaned',
            warning='PDB Files Changed, should re-clean'
        )
        file_status(
            name='mut_calc',
            error='Mutations Not Calculated',
            success='Mutations Calculated',
            warning='PDB Files Changed, should re-calculate'
        )
        file_status(
            name='depth',
            error='Residue Depth Not Calculated',
            success='Residue Depth Calculated',
            warning='PDB Files Changed, should re-calculate'
        )
        file_status(
            name='breakdown',
            error='Energy Breakdown Not Calculated',
            success='Energy Breakdown Calculated',
            warning='PDB Files Changed, should re-calculate'
        )

    pages[selected]()


if __name__ == '__main__':
    os.environ["NUMEXPR_MAX_THREADS"] = '8'
    main()
