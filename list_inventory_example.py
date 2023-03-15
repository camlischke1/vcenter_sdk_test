from decouple import config
import requests
import urllib3
from com.vmware.vcenter.vm_client import Tools
from vmware.vapi.vsphere.client import create_vsphere_client
from pprint import pprint

# uses what is set in .env file to define these global variables
ip = config('VCENTER_IP')
user = config('VCENTER_USER')
pwd = config('VCENTER_PASS')

#initiates connection to vcenter, leave this as template
session = requests.session()
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
vsphere_client = create_vsphere_client(server=ip, username=user, password=pwd, session=session)

#change whatever you want to do down here
vmlist = vsphere_client.vcenter.VM.list()
pprint(vmlist)

