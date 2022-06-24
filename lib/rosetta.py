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
