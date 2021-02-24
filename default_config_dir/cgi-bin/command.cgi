#!/usr/bin/env python

import sys
import os
import subprocess
import urllib
import urllib3
import shlex

if __name__ == '__main__':
    try:
        if os.getenv('PATH_INFO', '') == '/prompt':
            print('w3m-control: BACK')
            print('w3m-control: PROMPT file:/cgi-bin/{}?%s "[Command]:'.format(sys.argv[0].split('/')[-1]))
            print()
            exit(0)
        if os.path.exists(os.getenv('W3M_TEMP', '')):
            with open(os.path.join(os.getenv('W3M_TEMP'), 'commands.txt'), 'a') as f:
                f.write(os.getenv('QUERY_STRING', '') + os.linesep)
                # end with f
        command_args = shlex.split(os.path.expandvars(os.path.expanduser(urllib.parse.unquote_plus(os.getenv('QUERY_STRING', '')))))
        if len(command_args) < 1:
            print(os.linesep.join((
                'w3m-control: BACK',
                'w3m-control: MESSAGE ERROR: no command given',
                ''
            )))
            exit(0)
        command = None
        for directory in os.getenv('W3M_CMD_PATH', os.path.join(os.getenv('W3M_CONFIG_HOME', ''), 'cmd')).split(os.pathsep):
            command_path = os.path.join(directory, command_args[0])
            if os.access(command_path, os.X_OK):
                command = command_path
                break
            # end for directory
        if command is None:
            print(os.linesep.join((
                'w3m-control: BACK',
                'w3m-control: MESSAGE ERROR: command "{}" not found'.format(command_args[0]),
                ''
            )))
            exit(0)
        if os.getenv('W3M_URL', '')[:7] == 'file://' and os.path.isdir(os.getenv('W3M_URL', '')[7:]):
            os.chdir(os.getenv('W3M_URL', '')[7:])
        proc = subprocess.Popen([command, *command_args[1:]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_status = proc.wait()
        if proc_status != 0:
            print(os.linesep.join([
                'HTTP/2 404 ERROR',
                'Content-Type: text/plain; charset=utf-8',
                '',
                'ERROR ({})'.format(proc_status),
                '',
                *[line.decode().rstrip() for line in proc.stderr.readlines()]
            ]))
        else:
            print(proc.stdout.read().decode())
        proc.stdout.close()
        proc.stderr.close()
    except Exception as err:
        print(os.linesep.join([
            'HTTP/2 404 ERROR',
            'Content-Type: text/plain; charset=utf-8',
            '',
            'ERROR: {}'.format(err)
        ]))
    # end main
