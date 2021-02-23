#!/bin/bash

cat << _END_
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8

<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta lang="en" />
<title>W3M Environment</title>
</head>
<body>
<h1><center>W3M Environment</center></h1>
<ul>$(IFS=$'\r\n'; for var in $(env | grep 'W3M_'); do echo "<li>$var</li>"; done)</ul>
</body>
</html>
_END_

