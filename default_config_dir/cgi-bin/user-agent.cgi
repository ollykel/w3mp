#!/usr/bin/env zsh
# toggles user agent

user_agents_file="$HOME/.w3m/user-agents.txt"

if [[ -f "${user_agents_file}" ]]; then
	IFS=$'\r\n' user_agents=($(<"${user_agents_file}"))
fi

if [[ ! "${user_agents}" ]]; then
	user_agents[1]='Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/1.1.1d'
fi

if [[ "${PATH_INFO}" = '/select' ]]; then
	if [[ "${REQUEST_METHOD}" = 'POST' ]]; then
		for var in $(IFS='&' read -Ae); do
			IFS='=' read key val <<< "${var}"
			if [[ "${key}" = 'index' ]]; then
				W3M_USER_AGENT="${val}"
				curr_user_agent="${user_agents[${W3M_USER_AGENT}]}"
			elif [[ "${key}" = 'new_agent' && "${val}" ]]; then
				curr_user_agent="${val}"
				let "W3M_USER_AGENT = ${#user_agents} + 1"
				python << _EOF_ | read curr_user_agent
from urllib import parse as urlparse

out = urlparse.unquote_plus("${curr_user_agent}")
print(out)
_EOF_
				echo "${curr_user_agent}" >> "${user_agents_file}"
				break
			fi
		done
		cat << _EOF_
w3m-control: BACK
w3m-control: BACK
w3m-control: SETENV W3M_USER_AGENT=${W3M_USER_AGENT}
w3m-control: SET_OPTION user_agent=${curr_user_agent}

_EOF_
	else
		cat << _EOF_
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Date: $(date --utc)
w3m-control: NEXT_LINK

<!DOCTYPE html>
<html>
	<head>
		<meta charset="utf-8" />
		<meta lang="en" />
		<title>Select User Agent</title>
	</head>
	<body>
		<center>
		<form method="POST">
		<h1>Select a User Agent</h1>
		<select name="index">
			$(for i in {1..${#user_agents}}; do
				echo $'\t\t\t'"<option value=\"$i\">(${i}) ${user_agents[$i]}</option>"
			done)
		</select>
		<h2>OR add a new user agent</h2>
		<input name="new_agent" type="text" size="50" />
		<p>Current user agent: (${W3M_USER_AGENT}) ${${user_agents[${W3M_USER_AGENT}]}}</p>
		</center>
	</body>
</html>
_EOF_
	fi
	exit 0
fi

if [[ ! "${W3M_USER_AGENT}" ]]; then
	W3M_USER_AGENT='1'
else
	let "W3M_USER_AGENT = ${W3M_USER_AGENT} + 1"
	if [[ "${W3M_USER_AGENT}" -gt ${#user_agents} ]]; then
		W3M_USER_AGENT='1'
	fi
fi

curr_user_agent="${user_agents[$W3M_USER_AGENT]}"

cat << _END_
w3m-control: BACK
w3m-control: SETENV W3M_USER_AGENT=${W3M_USER_AGENT}
w3m-control: SET_OPTION user_agent=${curr_user_agent}

_END_

