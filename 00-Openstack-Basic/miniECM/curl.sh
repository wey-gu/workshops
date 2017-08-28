# Get TOKEN

curl -v -s -X POST http://controller:5000/v3/auth/tokens?nocatalog  -H "Content-Type: application/json" -d '{ "auth": { "identity": { "methods": ["password"],"password": {"user": {"domain": {"name": "'"Default"'"},"name": "'"demo"'", "password": "'"demo"'"} } }, "scope": { "project": { "domain": { "name": "'"Default"'" }, "name":  "'"demo"'" } } }}' 



curl -i -X POST \
-H "Accept: application/json" \
-H "Content-Type: application/json" \
-H "X-Auth-Token: $AUTH_TOKEN" \
-H "X-Project-Id: cb015df53fb34d90b077e4c36ce35826" \
-d  '{"stack_name": "Stack0", "disable_rollback": true,"parameters": {"NetID":"152a4a85-dc52-4c62-9bbd-742eb4f7b8fa"},"template_url": "http://controller/HOT-vAPG.yml","timeout_mins": 60}' \
-s http://controller:8004/v1/cb015df53fb34d90b077e4c36ce35826/stacks

curl -s -H "X-Auth-Token: $OS_TOKEN" http://controller:8774/v2.1/flavors/0 

curl -s -H "X-Auth-Token: $OS_TOKEN" -H "tenent_id: cb015df53fb34d90b077e4c36ce35826" http://controller:8004/v1/cb015df53fb34d90b077e4c36ce35826/build_info