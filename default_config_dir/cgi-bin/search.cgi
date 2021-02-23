#!/bin/bash

search_engine_file="${W3M_CONFIG_HOME}/search-engines.yaml"

# defaults
prompt_cmd='PROMPT'

if [[ "${PATH_INFO}" = '/newtab' ]]; then
	prompt_cmd='PROMPT_TAB'
fi

if [[ ! -f "${search_engine_file}" ]]; then
	cat << _EOF_
w3m-control: BACK
w3m-control: MESSAGE ERROR: could not find search engine file (${search_engine_file})

_EOF_
	exit 0
fi

# parse search engine file
IFS=$'\n\r' search_engine_lines=($(cat "${search_engine_file}"))
unset search_engines search_engine_names
declare -A search_engines
declare -A search_engine_names
idx=1
for line in ${search_engine_lines[*]}; do
	IFS=: read names engine <<< "${line}"
	IFS=', '; names=(${names})
	search_engines[${idx}]="${engine}"
	search_engine_names[${idx}]="${names[0]}"
	for name in ${names[*]}; do
		search_engines[${name}]="${engine}"
		search_engine_names[${name}]="${names[0]}"
	done
	let 'idx += 1'
	IFS=$'\n\r'
done

if [[ ${QUERY_STRING} ]]; then
	engine_id="${QUERY_STRING}"
elif [[ ${W3M_KEYNUM} ]]; then
	engine_id="${W3M_KEYNUM}"
else
	engine_id=1
fi

engine="${search_engines[${engine_id}]}"

if [[ ! "${engine}" ]]; then
	cat << _EOF_
w3m-control: BACK
w3m-control: MESSAGE No search engine "${engine_id}" found (${#search_engine_lines[*]} available)

_EOF_
else
	cat << _EOF_
w3m-control: BACK
w3m-control: ${prompt_cmd} ${engine} "(search ${search_engine_names[${engine_id}]}):"

_EOF_
fi
