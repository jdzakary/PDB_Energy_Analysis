import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))
from utility import load_text


def main():
    st.title('Energetic Analysis Tools')
    st.header('Introduction')
    st.write(load_text('home', 'introduction'))
    st.header('External Programs')
    st.write(load_text('home', 'external_tools'))


if __name__ == '__main__':
    main()
