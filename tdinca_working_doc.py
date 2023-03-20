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
import time
import logging
from samples.vsphere.vcenter.helper.guest_helper import \
    (wait_for_guest_info_ready, wait_for_guest_power_state)

from samples.vsphere.vcenter.helper import datacenter_helper

## PUT DEFINITIONS HERE !!!

# confirmed
def list_vms_formatted(client):
        list = client.vcenter.VM.list()

        for i in range(len(list)):
            ### Split the initial list
            listSplit = str(list[i]).split(", ")


            vmInitial = listSplit[0].strip()
            vmInitial = vmInitial.replace(" ", "")
            vmNext = []
            for letter in vmInitial:
                vmNext.append(letter)
            vmNext = vmNext[1:-1]
            vmNext.insert(3, " ")

            vm = ''.join([str(elem) for elem in vmNext])
            

            nameInitial = listSplit[1].strip()
            nameInitial = nameInitial.replace(" ", "")
            nameNext = []
            for letter in nameInitial:
                 nameNext.append(letter)
            nameNext.insert(5, " ")
            
            name = ''.join([str(elem) for elem in nameNext])


            power_stateInital = listSplit[2].strip()
            power_stateInital = power_stateInital.replace(" ", "")
            power_stateNext = []
            for letter in power_stateInital:
                 power_stateNext.append(letter)
            power_stateNext.insert(12, " ")
            power_state = ''.join([str(elem) for elem in power_stateNext])

            cpu_countInitial = listSplit[3].strip()
            cpu_countInitial = cpu_countInitial.replace(" ", "")
            cpu_countNext = []
            for letter in cpu_countInitial:
                 cpu_countNext.append(letter)
            cpu_countNext.insert(10, " ")
            cpu_count = ''.join([str(elem) for elem in cpu_countNext])

            memory_size_mibInitial = listSplit[4].strip()
            memory_size_mibInitial = memory_size_mibInitial.replace(" ", "")
            memory_size_mibNext = []
            for letter in memory_size_mibInitial:
                 memory_size_mibNext.append(letter)
            memory_size_mibNext.insert(16, " ")
            del memory_size_mibNext[-1] ### Remove Value at Last Index
            memory_size_mib = ''.join([str(elem) for elem in memory_size_mibNext])

            ### Spacing Formatting ###
            vmSpacing = "  "
            if len(vmNext) < 11:
                 vmSpacing += " "

            nameSpacing = ""
            nameLength = len(nameNext[5:len(nameNext)])
            for i in range(26 - nameLength):
                 nameSpacing += " "

            cpuSpacing = "  "
            if len(cpu_countNext) < 13:
                 cpuSpacing += " "
            
            powerSpacing = ""
            if power_stateNext[-1] == 'N':
                 powerSpacing += "    "
            elif power_stateNext[-1] == 'F':
                 powerSpacing += "   "


            print(vm, vmSpacing, name, nameSpacing, power_state, powerSpacing, cpu_count, cpuSpacing, memory_size_mib)
        
        return list
        

def create_vm(client, 
              datacenter_name=None,
              vm_folder_name=None,
              datastore_name=None,
              guest_os=None,
              vm_name=None,
              placement_spec=None,
              standard_network=None,
              iso_datastore_path=None       #must be in format "[datastore_name] path/without/starting/slash"
              ):

        if not placement_spec:
            placement_spec = vm_placement_helper.get_placement_spec_for_resource_pool(
                client,
                datacenter_name,
                vm_folder_name,
                datastore_name)


        """
        Create an exhaustive VM.

        Using the provided PlacementSpec, create a VM with a selected Guest OS
        and provided name.

        Create a VM with the following configuration:
        * Hardware Version = VMX_11 (for 6.0)
        * CPU (count = 2, coresPerSocket = 2, hotAddEnabled = false,
        hotRemoveEnabled = false)
        * Memory (size_mib = 2 GB, hotAddEnabled = false)
        * 3 Disks and specify each of the HBAs and the unit numbers
          * (capacity=40 GB, name=<some value>, spaceEfficient=true)
        * Specify 2 ethernet adapters, one using a Standard Portgroup backing and
        the
          * nic2: Specify Ethernet (macType=GENERATED)
        * 1 CDROM (type=ISO_FILE, file="os.iso", startConnected=true)
        * 1 Serial Port (type=NETWORK_SERVER, file="tcp://localhost/16000",
        startConnected=true)
        * 1 Parallel Port (type=HOST_DEVICE, startConnected=false)
        * 1 Floppy Drive (type=CLIENT_DEVICE)
        * Boot, type=BIOS
        * BootDevice order: CDROM, DISK, ETHERNET

        Use guest and system provided defaults for remaining configuration settings.
        """
        GiB = 1024 * 1024 * 1024
        GiBMemory = 1024

        vm_create_spec = VM.CreateSpec(
            guest_os=guest_os,
            name=vm_name,
            placement=placement_spec,
            hardware_version=Hardware.Version.VMX_11,
            cpu=Cpu.UpdateSpec(count=2,
                               cores_per_socket=1,
                               hot_add_enabled=False,
                               hot_remove_enabled=False),
            memory=Memory.UpdateSpec(size_mib=2 * GiBMemory,
                                     hot_add_enabled=False),
            disks=[
                Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                                scsi=ScsiAddressSpec(bus=0, unit=0),
                                new_vmdk=Disk.VmdkCreateSpec(name='boot',
                                                             capacity=40 * GiB))
            ],
            nics=[
                Ethernet.CreateSpec(
                    start_connected=True,
                    mac_type=Ethernet.MacAddressType.GENERATED,
                    backing=Ethernet.BackingSpec(
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=standard_network)),
            ],
            cdroms=[
                Cdrom.CreateSpec(
                    start_connected=True,
                    backing=Cdrom.BackingSpec(type=Cdrom.BackingType.ISO_FILE,
                                              iso_file=iso_datastore_path)
                )
            ],
            boot=Boot.CreateSpec(type=Boot.Type.BIOS,
                                 delay=0,
                                 enter_setup_mode=False
                                 ),
            boot_devices=[
                BootDevice.EntryCreateSpec(BootDevice.Type.CDROM),
                BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
                BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET)
            ]
        )
        print('# Example: create_exhaustive_vm: Creating a VM using spec\n-----')
        print(pp(vm_create_spec))
        print('-----')

        vm = client.vcenter.VM.create(vm_create_spec)

        print("create_exhaustive_vm: Created VM '{}' ({})".format(vm_name,vm))

        vm_info = client.vcenter.VM.get(vm)
        print('vm.get({}) -> {}'.format(vm, pp(vm_info)))

        return vm


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


# confirmed
def power_on(client, vm_name):
    vm = get_vm(client, vm_name)

    if not vm:
        raise Exception('Sample requires an existing vm with name ({}).'
                        'Please create the vm first.'.format(vm_name))
    print("Using VM '{}' ({}) for Power Sample".format(vm_name, vm))

    # Get the vm power state
    print('\n# Example: Get current vm power state')
    status = client.vcenter.vm.Power.get(vm)
    print('vm.Power.get({}) -> {}'.format(vm, pp(status)))

    if status == Power.Info(state=Power.State.POWERED_OFF,
                clean_power_off=True) or status == Power.Info(state=Power.State.SUSPENDED,
                clean_power_off=True) or status == Power.Info(
                state=Power.State.POWERED_OFF) or status == Power.Info(
                state=Power.State.SUSPENDED):
        print('# Example: Power on the vm')
        client.vcenter.vm.Power.start(vm)
        print('vm.Power.start({})'.format(vm))
    else:
         print('vm.Power.start({}) failed. VM already powered on.'.format(vm))




# confirmed
def power_off(client, vm_name):
    vm = get_vm(client, vm_name)

    if not vm:
        raise Exception('Sample requires an existing vm with name ({}).'
                        'Please create the vm first.'.format(vm_name))
    print("Using VM '{}' ({}) for Power Sample".format(vm_name, vm))

    # Get the vm power state
    print('\n# Example: Get current vm power state')
    status = client.vcenter.vm.Power.get(vm)
    print('vm.Power.get({}) -> {}'.format(vm, pp(status)))

    # Power off the vm if it is on
    if status == Power.Info(state=Power.State.POWERED_ON):
        print('\n# Example: VM is powered on, power it off')
        client.vcenter.vm.Power.stop(vm)
        print('vm.Power.stop({})'.format(vm))



def power_suspend(client, vm_name):
    vm = get_vm(client, vm_name)

    if not vm:
        raise Exception('Sample requires an existing vm with name ({}).'
                        'Please create the vm first.'.format(vm_name))
    print("Using VM '{}' ({}) for Power Sample".format(vm_name, vm))

    # Get the vm power state
    print('\n# Example: Get current vm power state')
    status = client.vcenter.vm.Power.get(vm)
    print('vm.Power.get({}) -> {}'.format(vm, pp(status)))

    # Suspend the vm if it is on
    if status == Power.Info(state=Power.State.POWERED_ON):
        print('\n# Example: VM is powered on, suspending')
        client.vcenter.vm.Power.suspend(vm)
        print('vm.Power.suspend({})'.format(vm))

#confirmed
def get_guest_info(client, vm_name, force_power_on=False):
        vm = get_vm(client, vm_name)
        if not vm:
            raise Exception('Sample requires an existing vm with name ({}).'
                            'Please create the vm first.'.format(vm_name))
        print("Using VM '{}' ({}) for Guest Info Sample".format(vm_name, vm))


        # power on the VM if necessary and specified
        status = client.vcenter.vm.Power.get(vm)
        if status != Power.Info(state=Power.State.POWERED_ON) and force_power_on:
            print('You selected force power on. Powering on VM.')
            client.vcenter.vm.Power.start(vm)
        elif status != Power.Info(state=Power.State.POWERED_ON) and force_power_on==False:
            raise Exception('The VM you specified is turned off. '+
                            'To turn on, try again by specifying get_guest_info(client, vm_name, force_power_on=True')

        # wait for guest info to be ready
        wait_for_guest_info_ready(client, vm, 600)

        # get the Identity
        identity = client.vcenter.vm.guest.Identity.get(vm)
        print('vm.guest.Identity.get({})'.format(vm))
        print('Identity: {}'.format(pp(identity)))

        # get the local filesystem info
        local_filesysteem = client.vcenter.vm.guest.LocalFilesystem.get(vm)
        print('vm.guest.LocalFilesystem.get({})'.format(vm))
        print('LocalFilesystem: {}'.format(pp(local_filesysteem)))


#confirmed
def get_ip(client,vm_name):
        vm = get_vm(client, vm_name)
        if not vm:
            raise Exception('Sample requires an existing vm with name ({}).'
                            'Please create the vm first.'.format(vm_name))
        print("Using VM '{}' ({}) for Guest Info Sample".format(vm_name, vm))


        status = client.vcenter.vm.Power.get(vm)
        if status != Power.Info(state=Power.State.POWERED_ON):
            raise Exception('The VM you specified is turned off.')
        
        identity = client.vcenter.vm.guest.Identity.get(vm)
        print(identity.ip_address)

        return identity.ip_address


#confirmed
def get_macs(client,vm_name):
        vm = get_vm(client, vm_name)
        if not vm:
            raise Exception('Sample requires an existing vm with name ({}).'
                            'Please create the vm first.'.format(vm_name))
        print("Using VM '{}' ({}) for Guest Info Sample".format(vm_name, vm))


        status = client.vcenter.vm.Power.get(vm)
        if status != Power.Info(state=Power.State.POWERED_ON):
            raise Exception('The VM you specified is turned off.')
        
        nic_list = client.vcenter.vm.hardware.Ethernet.list(vm)
        mac_list = []
        for i in range(len(nic_list)):
            mac_list.append(client.vcenter.vm.hardware.Ethernet.get(vm,nic_list[i].nic).mac_address)
            print(client.vcenter.vm.hardware.Ethernet.get(vm,nic_list[i].nic).mac_address)

        return mac_list

#confirmed
def get_network_backing(client,
                        porggroup_name,
                        datacenter_name,
                        portgroup_type):
    """
    Gets a standard portgroup network backing for a given Datacenter
    Note: The method assumes that there is only one standard portgroup
    and datacenter with the mentioned names.
    """
    datacenter = datacenter_helper.get_datacenter(client, datacenter_name)
    if not datacenter:
        print("Datacenter '{}' not found".format(datacenter_name))
        return None

    filter = Network.FilterSpec(datacenters=set([datacenter]),
                                names=set([porggroup_name]),
                                types=set([portgroup_type]))
    network_summaries = client.vcenter.Network.list(filter=filter)

    if len(network_summaries) > 0:
        network = network_summaries[0].network
        print("Selecting {} Portgroup Network '{}' ({})".
              format(portgroup_type, porggroup_name, network))
        return network
    else:
        print("Portgroup Network not found in Datacenter '{}'".
              format(datacenter_name))
        return None


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
    vm_name = "tdinca_TEST"

    #initiates connection to vcenter, leave this as template
    session = requests.session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    client = create_vsphere_client(server=esx_ip, username=user, password=pwd, session=session)

    #change whatever you want to do down here

    # create_vm(client = client, 
    #            datacenter_name = datacenter_name,
    #            vm_folder_name = vm_folder,
    #            datastore_name = datastore_name,
    #            guest_os=os_tag,
    #            vm_name=vm_name,
    #            standard_network=network_id,
    #            iso_datastore_path = iso_datastore_path
    #            )

    #power_off(client, vm_name)
    #power_on(client,vm_name)
    #power_suspend(client,vm_name)
    #delete_vm(client,vm_name)
    list_vms_formatted(client)

    get_ip(client, "vcenter")
    get_macs(client, "KYPO")

    get_network_backing(client, "NERVE", datacenter_name, 'STANDARD_PORTGROUP')
    # get_network_backing(client, "DIB-Inside", datacenter_name)

if __name__ == '__main__':
    main()