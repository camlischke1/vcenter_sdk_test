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
from pyVmomi import vim
from samples.vsphere.common.ssl_helper import get_unverified_session
from samples.vsphere.common.sample_util import pp
from samples.vsphere.vcenter.helper import network_helper
from samples.vsphere.vcenter.helper import vm_placement_helper, datacenter_helper
from samples.vsphere.vcenter.helper.vm_helper import get_vm
import time
import logging
from samples.vsphere.vcenter.helper.guest_helper import \
    (wait_for_guest_info_ready, wait_for_guest_power_state)
from samples.vsphere.contentlibrary.lib.cls_api_helper import ClsApiHelper
from com.vmware.vcenter.ovf_client import LibraryItem
from samples.vsphere.common.service_manager_factory import ServiceManagerFactory
from samples.vsphere.contentlibrary.lib.cls_api_client import ClsApiClient
from com.vmware.content.library.item.updatesession_client import (
    File as UpdateSessionFile, PreviewInfo, WarningType, WarningBehavior)
from com.vmware.content.library.item_client import UpdateSessionModel
from samples.vsphere.common.id_generator import generate_random_uuid


## PUT DEFINITIONS HERE !!!

# confirmed
def list_vms(client):
        list = client.vcenter.VM.list()
        pprint(list)
        return list



def get_network_id(client,
                        network_name,
                        datacenter_name):
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
                                names=set([network_name]))
    network_summaries = client.vcenter.Network.list(filter=filter)

    if len(network_summaries) > 0:
        network = network_summaries[0].network
        print("Selecting Network '{}' ({})".
              format(network_name, network))
        return network
    else:
        print("Portgroup Network not found in Datacenter '{}'".
              format(datacenter_name))
        return None


        

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
def get_state(client,vm_name):
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
        return True
    else:
        return False

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
def create_vm_from_iso(client, yaml_file,turn_on=False):
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
        for i in range(config['vm']['disks']):
                current_disk = "disk" + str(i+1)
                disk_specs.append(Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec(name=config['vm'][current_disk]['name'],
                                                  capacity=config['vm'][current_disk]['capacity'] * GiB)))
            


        nic_specs = []
        for i in range(config['vm']['nics']):
            current_nic = "nic" + str(i+1)
            nic_specs.append(Ethernet.CreateSpec(
                    start_connected=True,
                    mac_type=Ethernet.MacAddressType.GENERATED,
                    backing=Ethernet.BackingSpec(
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=get_network_id(client,config['vm'][current_nic]['network'],config['prereqs']['datacenter_name']))))



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
        
        if turn_on:
            power_on(client,config['vm']['vm_name'])
        return vm


def import_ova_to_ovf(yaml_file,server=None, username=None, password=None):
        servicemanager = ServiceManagerFactory.get_service_manager(server,
                                                         username,
                                                         password,
                                                         skip_verification=True)
        cls_client = ClsApiClient(servicemanager)
        helper = ClsApiHelper(cls_client, skip_verification=True)


        with open(yaml_file, 'r') as file:
            config = yaml.safe_load(file)

        # Build the storage backing for the library to be created using given datastore name
        datastore_name = config['prereqs']['datastore_name']
        storage_backings = helper.create_storage_backings(service_manager=servicemanager,
                                                               datastore_name=datastore_name)

        # Create a local content library backed by the VC datastore using vAPIs
        local_lib_id = helper.create_local_library(storage_backings, config['vm']['lib_name'])

        # Create a new library item in the content library for uploading the files
        lib_item_id = helper.create_library_item(library_id=local_lib_id,
                                                           item_name=config['vm']['destination_template_name'],
                                                           item_description='Sample template from ova file',
                                                           item_type='ovf')
        print('Library item created. ID: {0}'.format(lib_item_id))

        ova_file_map = helper.get_ova_file_map(config['vm']['current_relative_ova_dir'],
                                                    local_filename=config['vm']['current_ova_name'])
        # Create a new upload session for uploading the files
        # To ignore expected warnings and skip preview info check,
        # you can set create_spec.warning_behavior during session creation
        session_id = cls_client.upload_service.create(
            create_spec=UpdateSessionModel(library_item_id=lib_item_id),
            client_token=generate_random_uuid())
        helper.upload_files_in_session(ova_file_map, session_id)

        cls_client.upload_service.complete(session_id)
        cls_client.upload_service.delete(session_id)
        print('Uploaded ova file as an ovf template to library item {0}'.format(lib_item_id))


        

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