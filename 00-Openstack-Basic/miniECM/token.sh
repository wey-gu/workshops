curl -v -s -X POST http://controller:5000/v3/auth/tokens?nocatalog  -H "Content-Type: application/json" -d '{ "auth": { "identity": { "methods": ["password"],"password": {"user": {"domain": {"name": "'"Default"'"},"name": "'"demo"'", "password": "'"demo"'"} } }, "scope": { "project": { "domain": { "name": "'"Default"'" }, "name":  "'"demo"'" } } }}' 

