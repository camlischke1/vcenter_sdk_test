from decouple import config
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
from pprint import pprint
from com.vmware.vcenter.vm_client import Tools
from vmware.vapi.vsphere.client import create_vsphere_client

## put class definitions here
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

## put class definitions here
def list_vms(client):
        """
        List VMs present in server
        """
        return(client.vcenter.VM.list())
        

def create_vm(client, datacenter_name,vm_folder_name,datastore_name,std_portgroup_name,guest_os):
    
    placement_spec = vm_placement_helper.get_placement_spec_for_resource_pool(
            client,
            datacenter_name,
            vm_folder_name,
            datastore_name)

    # Get a standard network backing
    standard_network = network_helper.get_network_backing(
        client,
        std_portgroup_name,
        datacenter_name,
        Network.Type.STANDARD_PORTGROUP)

    boot_disk = Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                                scsi=ScsiAddressSpec(bus=0, unit=0),
                                new_vmdk=Disk.VmdkCreateSpec())
    data_disk = Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec())

    nic = Ethernet.CreateSpec(
        start_connected=True,
        backing=Ethernet.BackingSpec(
            type=Ethernet.BackingType.STANDARD_PORTGROUP,
            network=standard_network))

    boot_device_order = [
        BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET),
        BootDevice.EntryCreateSpec(BootDevice.Type.DISK)]

    vm_create_spec = VM.CreateSpec(name=self.vm_name,
                                    guest_os=guest_os,
                                    placement=self.placement_spec,
                                    disks=[boot_disk, data_disk],
                                    nics=[nic],
                                    boot_devices=boot_device_order)
    print('\n# Example: create_basic_vm: Creating a VM using spec\n-----')
    print(pp(vm_create_spec))
    print('-----')

    vm = self.client.vcenter.VM.create(vm_create_spec)

    print("create_basic_vm: Created VM '{}' ({})".format(self.vm_name, vm))

    vm_info = self.client.vcenter.VM.get(vm)
    print('vm.get({}) -> {}'.format(vm, pp(vm_info)))

    return vm

def cleanup(self):
    vm = get_vm(self.client, self.vm_name)
    if vm:
        state = self.client.vcenter.vm.Power.get(vm)
        if state == Power.Info(state=Power.State.POWERED_ON):
            self.client.vcenter.vm.Power.stop(vm)
        elif state == Power.Info(state=Power.State.SUSPENDED):
            self.client.vcenter.vm.Power.start(vm)
            self.client.vcenter.vm.Power.stop(vm)
        print("Deleting VM '{}' ({})".format(self.vm_name, vm))
        self.client.vcenter.VM.delete(vm)


def main():
    # uses what is set in .env file to define these global variables
    esx_ip = config('VCENTER_IP')
    user = config('VCENTER_USER')
    pwd = config('VCENTER_PASS')
    datacenter_name = config('DATACENTER')
    datastore_name = config('DATASTORE')
    guest_os = config('GUEST_OS')

    #initiates connection to vcenter, leave this as template
    session = requests.session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    vsphere_client = create_vsphere_client(server=esx_ip, username=user, password=pwd, session=session)

    #change whatever you want to do down here
    pprint(list_vms(vsphere_client))



if __name__ == '__main__':
    main()
