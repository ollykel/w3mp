#!/usr/bin/env zsh
# copies environment variable to clipboard

[[ ${PATH_INFO} ]] && buffer="${PATH_INFO[1,-1]}" || buffer='clipboard'

for var in $(IFS=+ read -Ae <<< "${QUERY_STRING}"); do
	val="$(printenv ${var})" && [[ ${val} ]] && break
done

cat << _EOF_
HTTP/1.1 200 OK
w3m-control: EXTERN /bin/echo -n "${val}" | xclip -selection ${buffer} -in && echo %s > /dev/null
w3m-control: BACK

_EOF_

