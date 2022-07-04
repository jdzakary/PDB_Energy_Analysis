from typing import List, Dict, Iterable
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Structure import Structure
import py3Dmol
from stmol import showmol
from io import StringIO
import streamlit as st


class WebStructure:
    def __init__(self, file_name: str):
        self.parser = PDBParser()
        self.parser.QUIET = True
        self.pdb_file: StringIO = st.session_state[f'pdb_{file_name}_clean']
        self.structure = self.__load_structure()
        self.text = self.__load_text()

    def __load_structure(self) -> Structure:
        structure = self.parser.get_structure(0, self.pdb_file)
        self.pdb_file.seek(0)
        return structure

    def __load_text(self) -> str:
        text = self.pdb_file.read()
        self.pdb_file.seek(0)
        return text


class WebViewer:
    def __init__(self, width: int = 800, height: int = 500):
        self.view = py3Dmol.view(width=width, height=height)
        self.structs: Dict[str, WebStructure] = {}
        self.id_struct: Dict[str, int] = {}
        self.width = width
        self.height = height

    def add_model(self, file_name: str):
        structure = WebStructure(file_name)
        self.structs[file_name] = structure
        self.id_struct[file_name] =\
            0 if not len(self.id_struct) else max(self.id_struct.values()) + 1
        self.view.addModel(structure.text, file_name)
        self.view.zoomTo()

    def show_cartoon(self, file_name: str, color: str):
        self.__set_style(
            {
                'model': self.id_struct[file_name]
            },
            {
                'cartoon': {
                    'color': color
                }
            }
        )

    def color_cartoon(self, file_name: str, resi: int, color: str):
        self.__set_style(
            {
                'model': self.id_struct[file_name],
                'resi': resi
            },
            {
                'cartoon': {
                    'color': color
                }
            }
        )

    def __set_style(self, criteria: dict, style: dict):
        self.view.setStyle(criteria, style)

    def show_sc(
        self,
        file_name: str,
        resi: Iterable[int],
        color_stick: str,
        color_cartoon: str
    ):
        self.__set_style(
            {
                'model': self.id_struct[file_name],
                'resi': list(resi),
                'not': {
                    'atom': ['N', 'CA', 'C', 'O']
                }
            },
            {
                'stick': {
                    'color': color_stick
                }
            }
        )
        self.__set_style(
            {
                'model': self.id_struct[file_name],
                'resi': list(resi),
                'or': [
                    {
                        'atom': 'CA'
                    },
                    {
                        'atom': 'N',
                        'resn': 'PRO'
                    }
                ],
            },
            {
                'stick': {
                    'color': color_stick
                },
                'cartoon': {
                    'color': color_cartoon
                }
            }
        )

    def set_background(self, color: str):
        self.view.setBackgroundColor(color)

    def center(self, file_name: str, resi: List[int]):
        self.view.center(
            {
                'model': self.id_struct[file_name],
                'resi': resi
            }
        )

    def show_hydrogen(
        self,
        file_name: str,
        resi: Iterable[int],
        color_stick: str
    ):
        self.__set_style(
            {
                'model': self.id_struct[file_name],
                'resi': list(resi),
                'elem': 'H'
            },
            {
                'stick': {
                    'color': color_stick
                }
            }
        )

    def show(self):
        showmol(self.view, width=self.width, height=self.height)
