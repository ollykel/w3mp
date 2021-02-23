#!/bin/bash

header="$(cut -d ',' -f 1 <<< "${QUERY_STRING}")"
data="$(cut -d ',' -f 2- <<< "${QUERY_STRING}")"
mime_type="$(sed -re 's#data:([0-9A-Za-z\._-]*/[0-9A-Za-z\._-]*).*#\1#' <<< "${header}")"

cat << _EOF_
HTTP/1.1 200 OK
Content-Type: ${mime_type}

_EOF_
base64 --decode <<< ${data}

