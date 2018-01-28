#!/usr/bin/python
import requests
import json
from config import auth_token

# netid = 152a4a85-dc52-4c62-9bbd-742eb4f7b8fa
# URL   = http://controller/HOT-vAPG.yml
# Name  = vAPG

def heatInstantiation(stackName,netID,templateURL):
    tenant_id = "cb015df53fb34d90b077e4c36ce35826"
    heat_url = "http://controller:8004/v1/%s" % tenant_id
    api_url = heat_url + "/stacks"

    headers = {'X-Auth-Token'      : auth_token,
                     'Accept'      : 'application/json', 
                     'Content-Type': 'application/json', 
                     'X-Project-Id': tenant_id
                     }
    payload = { "stack_name"    : stackName,
                "parameters"    : {"NetID" :netID},
                "template_url"  : templateURL
                }

    r = requests.post(api_url, data=json.dumps(payload), headers=headers)
    print  r.status_code
    #print  r.response
    return "Instantiation Started.... your laptop is about to be extreamly slow!!!"
