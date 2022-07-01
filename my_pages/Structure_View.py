import streamlit as st
import py3Dmol
from stmol import showmol
from io import StringIO
from utility import load_text
from typing import List, Dict, Iterable, Optional
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Structure import Structure


class WebStructure:
    def __init__(self, file_name: str):
        self.parser = PDBParser()
        self.parser.QUIET = True
        self.pdb_file: StringIO = st.session_state[f'pdb_{file_name}_clean']
        self.structure = self.__load_structure()
        self.text = self.__load_text()
        self.atom_map = self.__create_atom_map()

    def __load_structure(self) -> Structure:
        structure = self.parser.get_structure(0, self.pdb_file)
        self.pdb_file.seek(0)
        return structure

    def __load_text(self) -> str:
        text = self.pdb_file.read()
        self.pdb_file.seek(0)
        return text

    def __create_atom_map(self) -> Dict[int or str, List[int]]:
        mapping = {}
        counter = 1
        resi = 1
        mapping['back'] = []
        mapping['side'] = []
        mapping['attach'] = []
        for i in self.structure.get_residues():
            mapping[resi] = []

            for j in i.get_atoms():
                mapping[resi].append(counter)
                atom_name = j.get_full_id()[4][0]

                if atom_name in ['N', 'CA', 'C', 'O']:
                    mapping['back'].append(counter)
                else:
                    mapping['side'].append(counter)

                if atom_name == 'CA':
                    mapping['attach'].append(counter)
                elif i.resname == 'PRO' and atom_name == 'N':
                    mapping['attach'].append(counter)

                if j.element not in mapping.keys():
                    mapping[j.element] = []
                mapping[j.element].append(counter)

                counter += 1
            resi += 1
        return mapping

    def fetch_atoms(
        self,
        resi: Iterable[int],
        criteria: Optional[List[str]] = None
    ) -> List[int]:
        results = []
        for i in resi:
            if criteria:
                for j in self.atom_map[i]:
                    if all([j in self.atom_map[c] for c in criteria]):
                        results.append(j)
            else:
                results += self.atom_map[i]
        return results


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

    def show(self):
        # self.view.zoomTo()
        showmol(self.view, width=self.width, height=self.height)


def simple_show() -> None:
    color = st.color_picker('Background', '#E2DFDF')
    viewer = WebViewer()
    viewer.add_model('wild')
    viewer.add_model('variant')
    viewer.show_cartoon('wild', 'gray')
    viewer.show_cartoon('variant', 'blue')
    viewer.show_sc('wild', range(1, 15), 'green', 'gray')
    viewer.set_background(color)
    viewer.center('wild', [3, 4])
    viewer.show()


def check_files() -> bool:
    constraints = [
        'pdb_wild_clean' in st.session_state.keys(),
        'pdb_variant_clean' in st.session_state.keys()
    ]
    return all(constraints)


def main():
    st.title('Structure View')
    st.info(load_text('structure_view', 'align_warning'))
    if check_files():
        simple_show()
    else:
        st.error('Not all Requirements are Satisfied')
