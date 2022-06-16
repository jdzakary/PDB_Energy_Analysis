import pandas as pd
import os
import re


def renumber_pdb(
        filename: str,
        save_path: str
) -> None:
    """
    This function renumbers the records of a PDB file by a given
    offset
    :param filename:
        The input file
    :param save_path:
        The path to save the cleaned PDB
    :return:
        None
    """
    with open(filename, 'r') as file:
        raw = file.read().split('\n')
    rows = [x for x in raw if x[0:4] == 'ATOM']
    offset = 1 - find_start(rows[0])
    with open('temp.txt', 'w') as file:
        file.write('\n'.join(rows))
    data = pd.read_fwf('temp.txt', header=None, infer_nrows=2000)
    os.remove('temp.txt')
    data.columns = [
        'ATOM', 'atom_number', 'PDB_atom', 'resi_3', 'resi_1',
        'resi_number', 'A', 'B', 'C', 'D', 'E', 'atom'
    ]
    data['resi_number'] = data['resi_number'] + offset
    data['PDB_atom'] = data['PDB_atom'].apply(adjust_pdb)
    rows = []
    spacing = [4, 7, 5, 4, 2, 4, 12, 8, 8, 6, 6, 12]
    for row in data.iterrows():
        row_txt = ""
        counter = 0
        for column in row[1].values.tolist():
            row_txt += f'{column:>{spacing[counter]}}'
            counter += 1
        rows.append(row_txt)
    with open(save_path, 'w') as file:
        file.write('\n'.join(rows))


def adjust_pdb(x: str) -> str:
    initial = len(x)
    if initial == 1:
        x += '  '
    if initial == 2:
        x += ' '
    if x[0].isnumeric() and initial == 3:
        x += ' '
    return x


def find_start(data: str) -> int:
    start = data.find(re.findall(r'\w\w\w \w', data)[0]) + 5
    number = ''
    final = False
    while len(number) == 0 or not final:
        if data[start].isnumeric():
            number += data[start]
        elif len(number) > 0:
            final = True
        start += 1
    return int(number)


if __name__ == '__main__':
    pass
