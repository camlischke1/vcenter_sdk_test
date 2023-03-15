from decouple import config
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
from pprint import pprint
from decouple import config
import requests
import urllib3
from pprint import pprint
from com.vmware.vcenter.vm_client import Tools
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (
    Disk, Ethernet)
from com.vmware.vcenter.vm.hardware_client import ScsiAddressSpec
from com.vmware.vcenter.vm_client import (Power)
from com.vmware.vcenter_client import VM, Network
from vmware.vapi.vsphere.client import create_vsphere_client

from samples.vsphere.common.ssl_helper import get_unverified_session
from samples.vsphere.common import sample_cli
from samples.vsphere.common import sample_util
from samples.vsphere.common.sample_util import pp
from samples.vsphere.vcenter.helper import network_helper
from samples.vsphere.vcenter.helper import vm_placement_helper
from samples.vsphere.vcenter.helper.vm_helper import get_vm

## PUT DEFINITIONS HERE !!!

# confirmed
def list_vms(client):
        """
        List VMs present in server
        """
        list = client.vcenter.VM.list()
        pprint(list)
        return list


# confirmed
def delete_vm(client, vm_name):
        """
            Delete a VM using a predefined client.
            @param client: vsphere_client defined by vmware.vapi.vsphere.client.create_vsphere_client()
            @param vm_name: name of VM to be deleted
        """
        vm = get_vm(client, vm_name)
        if not vm:
            raise Exception('Sample requires an existing vm with name ({}).'
                            'Please create the vm first.'.format(vm_name))
        print("Deleting VM -- '{}-({})')".format(vm_name, vm))
        state = client.vcenter.vm.Power.get(vm)
        if state == Power.Info(state=Power.State.POWERED_ON):
            client.vcenter.vm.Power.stop(vm)
        elif state == Power.Info(state=Power.State.SUSPENDED):
            client.vcenter.vm.Power.start(vm)
            client.vcenter.vm.Power.stop(vm)
        client.vcenter.VM.delete(vm)
        print("Deleted VM -- '{}-({})".format(vm_name, vm))





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
    


if __name__ == '__main__':
    main()