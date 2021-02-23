#!/bin/bash

function print_msg() {
cat << _EOF_
w3m-control: BACK
w3m-control: MESSAGE ${1}

_EOF_
}

external_browser_file="${W3M_CONFIG_HOME}/external-browsers.yaml"

if [[ ! -f "${external_browser_file}" ]]; then
	print_msg "ERROR: Could not find external browser file at ${external_browser_file}"
	exit 0
fi

[[ ! ${W3M_KEYNUM} ]] && W3M_KEYNUM=1

IFS=$'\n\r' browsers=($(sed -re 's#[^\:]+\:\s*(.+)#\1#' < "${external_browser_file}"))

if [[ ${W3M_KEYNUM} -gt ${#browsers[*]} ]]; then
	print_msg "ERROR: No external browser #${W3M_KEYNUM} available (${#browsers[*]} browsers available)"
	exit 0
fi

cat << _EOF_
w3m-control: BACK
w3m-control: $([[ "${PATH_INFO}" = '/link' ]] && echo 'EXTERN_LINK' || echo 'EXTERN') ${browsers[${W3M_KEYNUM} - 1]}

_EOF_

