import pandas as pd
import os
from subprocess import Popen, PIPE


def simple_run(command: list) -> str:
    process = Popen(command, shell=False, stdout=PIPE)
    output = list()
    while True:
        output.append(process.stdout.readline().strip())
        if process.poll() is not None:
            break
    return '\n'.join([x.decode() for x in output])


def rosetta_simple(executable: str, args: list = None) -> str:
    command = [executable]
    if args:
        command += args
    log = simple_run(command)
    return log


def convert_outfile(
    file_name: str,
    save_path: str
) -> None:
    """
    Convert the output of rosetta_energy_breakdown into a usable CSV file
    :param file_name:
        The path of the .out file to read
    :param save_path:
        Where to save the .csv file
    :return:
    """
    with open(file_name, 'r') as file:
        data = file.read()
    lines = data.split('\n')
    spacer = lines[1].find(' 1 ') - 16
    lines[0] = lines[0][0:6] + ' '*spacer + lines[0][6:]

    with open('temp.txt', 'w') as file:
        file.write('\n'.join(lines))

    data = pd.read_fwf('temp.txt')
    data.drop(columns=['description', 'SCORE:', 'pose_id'], inplace=True)
    data.to_csv(save_path, index=False)
    os.remove('temp.txt')


def run(
    file_name: str,
    save_path: str,
    rosetta_executable: str,
    log_path: str
) -> None:
    """
    Run the rosetta_energy_breakdown protocol as a subprocess
    :param file_name:
        The input PDB file
    :param save_path:
        Where to save the .out file
    :param rosetta_executable:
        Fully qualified path to the rosetta executable being used
    :param log_path:
        Where to save the log file from Rosetta
    :return:
    """
    assert 'residue_energy_breakdown' in rosetta_executable
    options = [
        f'-in:file:s {file_name}',
        f'-out:file:silent {save_path}'
    ]
    log = rosetta_simple(rosetta_executable, options)
    with open(log_path, 'w') as file:
        file.write(log)
