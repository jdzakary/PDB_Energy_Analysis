import streamlit as st
import sys
import os
from PIL import Image
sys.path.append(os.path.dirname(__file__))
from utility import load_text


def clear_session():
    for key in st.session_state.keys():
        del st.session_state[key]


def load_logo():
    logo = Image.open('images/lab_logo.png')
    st.sidebar.image(logo, use_column_width=True)


def main():
    st.title('Energetic Analysis Tools')
    st.header('Introduction')
    st.write(load_text('home', 'introduction'))
    st.header('External Programs')
    st.write(load_text('home', 'external_tools'))
    st.header('Reset the Application')
    st.error('Warning! This will Clear all Data!')
    st.button('Reset', on_click=clear_session)
    #load_logo()


if __name__ == '__main__':
    main()
