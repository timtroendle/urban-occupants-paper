import subprocess

import click

import urbanoccupants as uo


@click.command()
@click.argument('path_to_jar')
@click.argument('path_to_input')
@click.argument('path_to_output')
@click.argument('path_to_config')
def run_simulation(path_to_jar, path_to_input, path_to_output, path_to_config):
    config = uo.read_simulation_config(path_to_config)
    cmd = ['java', '-jar', '-Xmx{}g'.format(config['java-heap-size']), str(path_to_jar),
           '-i', str(path_to_input), '-o', str(path_to_output),
           '-w', str(config['number-processes'])]
    popen = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    for stdout_line in iter(popen.stdout.readline, ""):
        print(stdout_line, end="")
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


if __name__ == '__main__':
    run_simulation()
