from decouple import config
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
from pprint import pprint

## put class definitions here
def list_vms(client):
        """
        List VMs present in server
        """
        return(client.vcenter.VM.list())
        



def main():
    # uses what is set in .env file to define these global variables
    esx_ip = config('VCENTER_IP')
    user = config('VCENTER_USER')
    pwd = config('VCENTER_PASS')
    datacenter_name = config('DATACENTER')
    datastore_name = config('DATASTORE')

    #initiates connection to vcenter, leave this as template
    session = requests.session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    vsphere_client = create_vsphere_client(server=esx_ip, username=user, password=pwd, session=session)

    #change whatever you want to do down here
    pprint(list_vms(vsphere_client))



if __name__ == '__main__':
    main()
