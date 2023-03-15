from decouple import config
import requests
import urllib3
from pprint import pprint
from com.vmware.vcenter.vm_client import Tools
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (
    Cpu, Memory, Disk, Ethernet, Cdrom, Serial, Parallel, Floppy, Boot)
from com.vmware.vcenter.vm.hardware_client import ScsiAddressSpec
from com.vmware.vcenter.vm_client import (Power,Hardware)
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



def main():
    # uses what is set in .env file to define these global variables
    esx_ip = config('VCENTER_IP')
    user = config('VCENTER_USER')
    pwd = config('VCENTER_PASS')
    datacenter_name = config('DATACENTER')
    datastore_name = config('DATASTORE')
    iso_datastore_path = "[" + datastore_name + "] ISOs/ubuntu-18.04.5-live-server-amd64.iso"
    network_id = "network-6009"       #ID for Orchestration 
    vm_folder = 'vcenter_api_test_folder'
    os_tag = "UBUNTU_64"
    vm_name = "Camtest"

    #initiates connection to vcenter, leave this as template
    session = requests.session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    client = create_vsphere_client(server=esx_ip, username=user, password=pwd, session=session)

    #change whatever you want to do down here
    



if __name__ == '__main__':
    main()