#!/usr/bin/python
from config import auth_token

tenant_id = "cb015df53fb34d90b077e4c36ce35826"
heat_url = "http://controller:8004/v1/%s" % tenant_id

# auth_token = "gAAAAABZoYB5PWN7Zq5xJLRu4WHT_OnzmlNGf56M5FzbLRNincqtUdvnXbNvruXXSIFX_l0WAkw0ewDgdBYpZ5MT0-OyT9UgDylG9IeBvYgPo_IZpNRYH-H16iedYM1BYw12N8udlK-XyifnYuWIRgkfYVKsCWPTXRBiLAEfez3XtZrgojT_CeI"

from heatclient.client import Client
heat = Client('1', endpoint=heat_url, token=auth_token)

from keystoneauth1 import loading
from keystoneauth1 import session
from heatclient import client
loader = loading.get_plugin_loader('password')

auth = loader.load_from_options(auth_url= "http://controller:5000/v3",
                                 username="demo",
                                 password="demo",
                                 project_id="demo")

sess = session.Session(auth=auth)
heat = client.Client('1', session=sess)
heat.stacks.list()
#heat.stacks.create(parameters="NetID=152a4a85-dc52-4c62-9bbd-742eb4f7b8fa",file=u"./HOT-vAPG.yml",name="testStack")