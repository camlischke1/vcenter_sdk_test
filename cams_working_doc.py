from decouple import config
import requests
import urllib3
import yaml
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
from samples.vsphere.common.sample_util import pp
from samples.vsphere.vcenter.helper import network_helper
from samples.vsphere.vcenter.helper import vm_placement_helper
from samples.vsphere.vcenter.helper.vm_helper import get_vm
import time
import logging
from samples.vsphere.vcenter.helper.guest_helper import \
    (wait_for_guest_info_ready, wait_for_guest_power_state)

## PUT DEFINITIONS HERE !!!

# confirmed
def list_vms(client):
        list = client.vcenter.VM.list()
        pprint(list)
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
def create_vm_from_yaml(client, yaml_file):
        with open(yaml_file, 'r') as file:
            config = yaml.safe_load(file)

        placement_spec = vm_placement_helper.get_placement_spec_for_resource_pool(
                    client,
                    config['prereqs']['datacenter_name'],
                    config['prereqs']['folder_name'],
                    config['prereqs']['datastore_name'])
        iso_datastore_path = "[" + config['prereqs']['datastore_name'] + "] " + config['vm']['iso_path']

        GiB = 1024 * 1024 * 1024
        GiBMemory = 1024

        disk_specs = []
        for i in range(1,config['vm']['disks']):
                current_disk = "disk" + str(i)
                disk_specs.append(Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                                scsi=ScsiAddressSpec(bus=0, unit=0),
                                new_vmdk=Disk.VmdkCreateSpec(name=config['vm'][current_disk]['name'],
                                                             capacity=config['vm'][current_disk]['capacity'] * GiB)))
            


        nic_specs = []
        for i in range(1,config['vm']['nics']):
            current_nic = "nic" + str(i)
            nic_specs.append(Ethernet.CreateSpec(
                    start_connected=True,
                    mac_type=Ethernet.MacAddressType.GENERATED,
                    backing=Ethernet.BackingSpec(
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=config['vm'][current_nic]['network'])))



        vm_create_spec = VM.CreateSpec(
            guest_os=config['vm']['guest_os'],
            name=config['vm']['vm_name'],
            placement=placement_spec,
            hardware_version=config['vm']['hardware_version'],
            cpu=Cpu.UpdateSpec(count=config['vm']['cpu_count'],
                               cores_per_socket=1,
                               hot_add_enabled=False,
                               hot_remove_enabled=False),
            memory=Memory.UpdateSpec(size_mib=config['vm']['memory'] * GiBMemory,
                                     hot_add_enabled=False),
            disks=disk_specs,
            nics=nic_specs,
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

        vm_info = client.vcenter.VM.get(vm)
        print('vm.get({}) -> {}'.format(vm, pp(vm_info)))
        print("create_exhaustive_vm: Created VM '{}' ({})".format(config['vm']['vm_name'],vm))
        return vm
     


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
    
    # create_vm(client = client, 
    #           datacenter_name = datacenter_name,
    #           vm_folder_name = vm_folder,
    #           datastore_name = datastore_name,
    #           guest_os=os_tag,
    #           vm_name=vm_name,
    #           standard_network=network_id,
    #           iso_datastore_path = iso_datastore_path
    #           )
    # power_off(client, vm_name)
    # power_on(client,vm_name)
    # power_suspend(client,vm_name)
    #delete_vm(client,'cams yaml test')
    # get_guest_info(client, 'caldera', force_power_on=False)
    # get_macs(client,'caldera')
    # list_vms(client)
    create_vm_from_yaml(client, 'vm_template.yaml')

if __name__ == '__main__':
    main()
