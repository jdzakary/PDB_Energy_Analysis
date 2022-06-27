import streamlit as st
import sys
import os
from PIL import Image
from my_pages import File_Upload, Interaction_Analysis, Residue_Depth
sys.path.append(os.path.dirname(__file__))
from utility import load_text


def clear_session() -> None:
    for key in st.session_state.keys():
        del st.session_state[key]


@st.cache
def load_logo() -> Image:
    logo = Image.open('images/lab_logo.png')
    return logo


def home() -> None:
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
    'Residue Depth': Residue_Depth.main
}


def main():
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
