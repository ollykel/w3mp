#!/bin/bash

session_tmp="${W3M_TEMP}"
cmd_hist_file="${session_tmp}/commands.txt"

if [[ ! -f "${cmd_hist_file}" ]]; then
	cat << _EOF_
w3m-control: BACK
w3m-control: MESSAGE ERROR: ${cmd_hist_file} not available

_EOF_
	exit 0
fi

[[ ${W3M_KEYNUM} ]] && num_commands="${W3M_KEYNUM}" || num_commands=1
IFS=$'\n\r' commands=($(tail --lines=${num_commands} < ${cmd_hist_file}))

commands_cgi="file:/cgi-bin/command.cgi"

cat << _EOF_
w3m-control: BACK
$(for cmd in ${commands[*]}; do
	echo "w3m-control: GOTO ${commands_cgi}?${cmd}"
done)

_EOF_

