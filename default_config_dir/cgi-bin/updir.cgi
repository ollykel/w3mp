#!/bin/bash

source ~/.w3m/lib/utils.sh

if [[ "${W3M_URL::7}" != 'file://' ]]; then
	print_msg 'ERROR: not in file mode'
	exit 0
fi

dest_dir="$(dirname "${W3M_URL:7}")"

cat << _EOF_
w3m-control: BACK
w3m-control: LOAD ${dest_dir}

_EOF_

