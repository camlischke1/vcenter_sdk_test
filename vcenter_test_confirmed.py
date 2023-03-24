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
from com.vmware.vcenter.vm_client import (Power,Hardware)
from com.vmware.vcenter_client import VM, Network
from vmware.vapi.vsphere.client import create_vsphere_client
from pyVmomi import vim
from samples.vsphere.common.sample_util import pp
from samples.vsphere.vcenter.helper import network_helper
from samples.vsphere.vcenter.helper import vm_placement_helper, datacenter_helper
from samples.vsphere.vcenter.helper.vm_helper import get_vm
from samples.vsphere.vcenter.helper.guest_helper import \
    (wait_for_guest_info_ready, wait_for_guest_power_state)
from samples.vsphere.contentlibrary.lib.cls_api_helper import ClsApiHelper
from com.vmware.vcenter.ovf_client import LibraryItem
from com.vmware.vcenter.vm_template_client import (
    LibraryItems as VmtxLibraryItem)
from samples.vsphere.common.service_manager_factory import ServiceManagerFactory
from samples.vsphere.contentlibrary.lib.cls_api_client import ClsApiClient
from com.vmware.content.library.item.updatesession_client import (
    File as UpdateSessionFile, PreviewInfo, WarningType, WarningBehavior)
from com.vmware.content.library.item_client import UpdateSessionModel
from samples.vsphere.common.id_generator import generate_random_uuid
from samples.vsphere.common.vim.helpers.vim_utils import (
    get_obj, get_obj_by_moId, poweron_vm, poweroff_vm, delete_object)

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

        # get the Network
        network = client.vcenter.vm.guest.Networking.get(vm)
        print('vm.guest.Networking.get({})'.format(vm))
        print('Networking: {}'.format(pp(network)))

        nic_summaries = client.vcenter.vm.hardware.Ethernet.list(vm)
        for nic_summary in nic_summaries:
            nic = nic_summary.nic
            nic_info = client.vcenter.vm.hardware.Ethernet.get(vm=vm, nic=nic)
            print('vm.hardware.Ethernet.get({}, {}) -> {}'.
                format(vm, nic, nic_info))

        # get the Customization
        cust = client.vcenter.vm.guest.Customization.get(vm)
        print('\nvm.guest.Customization.get({})'.format(vm))
        print('Customization: {}'.format(pp(cust)))
        
        # get the Operations
        cust = client.vcenter.vm.guest.Operations.get(vm)
        print('vm.guest.Operations.get({})'.format(vm))
        print('Operations: {}'.format(pp(cust)))

        ip = get_ip(client,vm_name)
        mac = get_macs(client,vm_name)
        print("Quick Access: \n Name: {}\n IP: {}\n MACS: {}".format(vm_name,ip,mac))


#confirmed
def get_ip(client,vm_name):
        vm = get_vm(client, vm_name)
        if not vm:
            raise Exception('Sample requires an existing vm with name ({}).'
                            'Please create the vm first.'.format(vm_name))


        status = client.vcenter.vm.Power.get(vm)
        if status != Power.Info(state=Power.State.POWERED_ON):
            raise Exception('The VM you specified is turned off.')
        
        identity = client.vcenter.vm.guest.Identity.get(vm)

        return identity.ip_address


#confirmed
def get_macs(client,vm_name):
        vm = get_vm(client, vm_name)
        if not vm:
            raise Exception('Sample requires an existing vm with name ({}).'
                            'Please create the vm first.'.format(vm_name))


        status = client.vcenter.vm.Power.get(vm)
        if status != Power.Info(state=Power.State.POWERED_ON):
            raise Exception('The VM you specified is turned off.')
        
        nic_list = client.vcenter.vm.hardware.Ethernet.list(vm)
        mac_list = []
        for i in range(len(nic_list)):
            mac_list.append(client.vcenter.vm.hardware.Ethernet.get(vm,nic_list[i].nic).mac_address)

        return mac_list
        


#confirmed
def create_vm_from_iso(yaml_file,conf_file,turn_on=False):
        with open(conf_file, 'r') as file:
            config = yaml.safe_load(file)

        with open(yaml_file, 'r') as file:
            template = yaml.safe_load(file)

        #creating vcenter client, different than APIclient
        session = requests.session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        client = create_vsphere_client(server=config['server'],
                                                username=config['user'],
                                                password=config['pass'], session=session)
        servicemanager = ServiceManagerFactory.get_service_manager(config['server'],
                                                                    config['user'],
                                                                    config['pass'],
                                                                    skip_verification=True)
        placement_spec = vm_placement_helper.get_placement_spec_for_resource_pool(
                    client,
                    template['prereqs']['datacenter_name'],
                    template['prereqs']['folder_name'],
                    template['prereqs']['datastore_name'])

        iso_datastore_path = "[" + template['prereqs']['datastore_name'] + "] " + template['vm']['iso_path']
        
        GiB = 1024 * 1024 * 1024
        GiBMemory = 1024

        disk_specs = []
        for i in range(template['vm']['disks']):
                current_disk = "disk" + str(i+1)
                disk_specs.append(Disk.CreateSpec(new_vmdk=Disk.VmdkCreateSpec(name=template['vm'][current_disk]['name'],
                                                  capacity=template['vm'][current_disk]['capacity'] * GiB)))
            


        nic_specs = []
        for i in range(template['vm']['nics']):
            current_nic = "nic" + str(i+1)
            nic_specs.append(Ethernet.CreateSpec(
                    start_connected=True,
                    mac_type=Ethernet.MacAddressType.GENERATED,
                    backing=Ethernet.BackingSpec(
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=get_network_id(client,template['vm'][current_nic]['network'],template['prereqs']['datacenter_name']))))



        vm_create_spec = VM.CreateSpec(
            guest_os=template['vm']['guest_os'],
            name=template['vm']['vm_name'],
            placement=placement_spec,
            hardware_version=template['vm']['hardware_version'],
            cpu=Cpu.UpdateSpec(count=template['vm']['cpu_count'],
                               cores_per_socket=1,
                               hot_add_enabled=False,
                               hot_remove_enabled=False),
            memory=Memory.UpdateSpec(size_mib=template['vm']['memory'] * GiBMemory,
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
        print("create_exhaustive_vm: Created VM '{}' ({})".format(template['vm']['vm_name'],vm))
        
        vm_obj = get_obj_by_moId(servicemanager.content,[vim.VirtualMachine], vm)
        print("Deployed VM '{0}' with ID: {1}".format(template['vm']['vm_name'],vm))

        # Print a summary of the deployed VM
        vm_summary = vm_obj.summary.config
        print('Guest OS: {0}'.format(vm_summary.guestId))
        print('{0} CPU(s)'.format(vm_summary.numCpu))
        print('{0} MB memory'.format(vm_summary.memorySizeMB))
        print('{0} disk(s)'.format(vm_summary.numVirtualDisks))
        print('{0} network adapter(s)'.format(vm_summary.numEthernetCards))

        if turn_on:
            power_on(client,template['vm']['vm_name'])
        return vm
     



#confirmed
def import_ova_to_ovf(yaml_file,conf_file):
        with open(conf_file, 'r') as file:
            config = yaml.safe_load(file)

        servicemanager = ServiceManagerFactory.get_service_manager(config['server'],
                                                         config['user'],
                                                         config['pass'],
                                                         skip_verification=True)
        cls_client = ClsApiClient(servicemanager)
        helper = ClsApiHelper(cls_client, skip_verification=True)


        with open(yaml_file, 'r') as file:
            template = yaml.safe_load(file)

        # Build the storage backing for the library to be created using given datastore name
        datastore_name = template['prereqs']['datastore_name']
        storage_backings = helper.create_storage_backings(service_manager=servicemanager,
                                                               datastore_name=datastore_name)


        if template['vm']['existing_library_id'] == "None":
            # Create a local content library backed by the VC datastore using vAPIs
            local_lib_id = helper.create_local_library(storage_backings, template['vm']['lib_name'])
            print('Content Library {0} created. ID: {1}'.format(template['vm']['lib_name'],local_lib_id))
        else:
            local_lib_id = template['vm']['existing_library_id']
            print('Content Library found. ID: {}'.format(local_lib_id))


        # Create a new library item in the content library for uploading the files
        lib_item_id = helper.create_library_item(library_id=local_lib_id,
                                                           item_name=template['vm']['template_name'],
                                                           item_description='Sample template from ova file',
                                                           item_type='ovf')
        print('Library item created. ID: {0}'.format(lib_item_id))

        ova_file_map = helper.get_ova_file_map(template['vm']['ova_current_full_path'],
                                                    local_filename=template['vm']['current_ova_name'])
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





# confirmed
def create_vm_from_ovf(yaml_file,conf_file):
        with open(conf_file, 'r') as file:
            config = yaml.safe_load(file)

        with open(yaml_file, 'r') as file:
            template = yaml.safe_load(file)

        #creating vcenter client, different than APIclient
        session = requests.session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        vcenter_client = create_vsphere_client(server=config['server'],
                                                username=config['user'],
                                                password=config['pass'], session=session)

        # this helps find resource pool id
        id_holder = vm_placement_helper.get_placement_spec_for_resource_pool(
            vcenter_client,
            template['prereqs']['datacenter_name'],
            template['prereqs']['folder_name'],
            template['prereqs']['datastore_name'])
        

        servicemanager = ServiceManagerFactory.get_service_manager(config['server'],
                                                         config['user'],
                                                         config['pass'],
                                                         skip_verification=True)
        client = ClsApiClient(servicemanager)
        helper = ClsApiHelper(client, skip_verification=True)
        

        deployment_target = LibraryItem.DeploymentTarget(id_holder.resource_pool)

        lib_item_id = helper.get_item_id_by_name(template['vm']['template_name'])
        assert lib_item_id
        ovf_summary = client.ovf_lib_item_service.filter(ovf_library_item_id=lib_item_id,
                                                              target=deployment_target)
        print('Found an OVF template :{0} to deploy.'.format(ovf_summary.name))

        print(ovf_summary)



        # Build the deployment spec
        deployment_spec = LibraryItem.ResourcePoolDeploymentSpec(
                                                                name=template['vm']['vm_name'],
                                                                annotation=ovf_summary.annotation,
                                                                accept_all_eula=True,
                                                                network_mappings=None,
                                                                storage_mappings=None,
                                                                default_datastore_id=id_holder.datastore)

        # Deploy the ovf template
        result = client.ovf_lib_item_service.deploy(lib_item_id,
                                                         deployment_target,
                                                         deployment_spec,
                                                         client_token=generate_random_uuid())

        # The type and ID of the target deployment is available in the deployment result.
        if result.succeeded:
            print('Deployment successful. Result resource: {0}, ID: {1}'
                  .format(result.resource_id.type, result.resource_id.id))
            vm_id = result.resource_id.id
            error = result.error
            if error is not None:
                for warning in error.warnings:
                    print('OVF warning: {}'.format(warning.message))

            vm = get_obj_by_moId(servicemanager.content,[vim.VirtualMachine], vm_id)
            print("Deployed VM '{0}' with ID: {1}".format(template['vm']['vm_name'],vm_id))

            # Print a summary of the deployed VM
            vm_summary = vm.summary.config
            print('Guest OS: {0}'.format(vm_summary.guestId))
            print('{0} CPU(s)'.format(vm_summary.numCpu))
            print('{0} MB memory'.format(vm_summary.memorySizeMB))
            print('{0} disk(s)'.format(vm_summary.numVirtualDisks))
            print('{0} network adapter(s)'.format(vm_summary.numEthernetCards))

            # Power on the VM and wait  for the power on operation to be completed
            vm_obj = get_obj_by_moId(servicemanager.content,
                                          [vim.VirtualMachine], vm_id)
            assert vm_obj is not None
            poweron_vm(servicemanager.content, vm_obj)

        else:
            print('Deployment failed.')
            for error in result.error.errors:
                print('OVF error: {}'.format(error.message))

#confirmed
def update_networking(yaml_file,conf_file):
        with open(conf_file, 'r') as file:
            config = yaml.safe_load(file)

        with open(yaml_file, 'r') as file:
            template = yaml.safe_load(file)


        #creating vcenter client, different than APIclient
        session = requests.session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        client = create_vsphere_client(server=config['server'],
                                                username=config['user'],
                                                password=config['pass'], session=session)
        servicemanager = ServiceManagerFactory.get_service_manager(config['server'],
                                                                    config['user'],
                                                                    config['pass'],
                                                                    skip_verification=True)

        vm = get_vm(client, template['vm']['vm_name'])
        nic_list = client.vcenter.vm.hardware.Ethernet.list(vm)
        print(nic_list)
        for i in range(len(nic_list)):
            print("Cleaning up {}".format(nic_list[i].nic))
            client.vcenter.vm.hardware.Ethernet.delete(vm,nic_list[i].nic)
        
        
        for i in range(template['vm']['nics']):
            current_nic = "nic" + str(i+1)
            nic = Ethernet.CreateSpec(
                    start_connected=True,
                    mac_type=Ethernet.MacAddressType.GENERATED,
                    backing=Ethernet.BackingSpec(
                        type=Ethernet.BackingType.STANDARD_PORTGROUP,
                        network=get_network_id(client,template['vm'][current_nic]['network'],template['prereqs']['datacenter_name'])))
            client.vcenter.vm.hardware.Ethernet.create(vm, nic)

        
        vm_obj = get_obj_by_moId(servicemanager.content,[vim.VirtualMachine], vm)
        print("Updated VM '{0}' with ID: {1}".format(template['vm']['vm_name'],vm))

        # Print a summary of the deployed VM
        vm_summary = vm_obj.summary.config
        print('Guest OS: {0}'.format(vm_summary.guestId))
        print('{0} CPU(s)'.format(vm_summary.numCpu))
        print('{0} MB memory'.format(vm_summary.memorySizeMB))
        print('{0} disk(s)'.format(vm_summary.numVirtualDisks))
        print('{0} network adapter(s)'.format(vm_summary.numEthernetCards))
        nic_list = client.vcenter.vm.hardware.Ethernet.list(vm)
        print(nic_list)

        return vm

        
     

#confirmed
def clone_to_template(yaml_file, conf_file):
        with open(conf_file, 'r') as file:
            config = yaml.safe_load(file)

        with open(yaml_file, 'r') as file:
            template = yaml.safe_load(file)


        #creating vcenter client, different than APIclient
        session = requests.session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        vsphere_client = create_vsphere_client(server=config['server'],
                                                username=config['user'],
                                                password=config['pass'], session=session)
        servicemanager = ServiceManagerFactory.get_service_manager(config['server'],
                                                                    config['user'],
                                                                    config['pass'],
                                                                    skip_verification=True)

        client = ClsApiClient(servicemanager)
        helper = ClsApiHelper(client, skip_verification=True)
        
        # Get the identifiers
        vm_id = get_vm(vsphere_client, template['vm']['vm_name'])
        placement_spec = vm_placement_helper.get_placement_spec_for_resource_pool(
                    vsphere_client,
                    template['prereqs']['datacenter_name'],
                    template['prereqs']['folder_name'],
                    template['prereqs']['datastore_name'])


        # Create a library
        if template['vm']['existing_library_id'] == "None":
            storage_backings = helper.create_storage_backings(servicemanager, template['prereqs']['datastore_name'])
            library_id = helper.create_local_library(storage_backings,template['vm']['lib_name'])
        else:
            library_id = template['vm']['existing_library_id']

        # Build the create specification
        create_spec = VmtxLibraryItem.CreateSpec()
        create_spec.source_vm = vm_id
        create_spec.library = library_id
        create_spec.name = template['vm']['template_name']
        create_spec.placement = VmtxLibraryItem.CreatePlacementSpec(resource_pool=placement_spec.resource_pool)

        # Create a new library item from the source VM
        item_id = client.vmtx_service.create(create_spec)
        print("Created VM template item '{0}' with ID: {1}".format(
            create_spec.name, item_id))

        # Retrieve the library item info
        info = client.vmtx_service.get(item_id)
        print('VM template guest OS: {0}'.format(info.guest_os))


# confirmed
def create_vm_from_template(yaml_file,conf_file,turn_on=False):
        with open(conf_file, 'r') as file:
            config = yaml.safe_load(file)

        with open(yaml_file, 'r') as file:
            template = yaml.safe_load(file)


        #creating vcenter client, different than APIclient
        session = requests.session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        vsphere_client = create_vsphere_client(server=config['server'],
                                                username=config['user'],
                                                password=config['pass'], session=session)
        servicemanager = ServiceManagerFactory.get_service_manager(config['server'],
                                                                    config['user'],
                                                                    config['pass'],
                                                                    skip_verification=True)

        client = ClsApiClient(servicemanager)
        helper = ClsApiHelper(client, skip_verification=True)
        
        # Get the identifiers
        id_holder = vm_placement_helper.get_placement_spec_for_resource_pool(
                    vsphere_client,
                    template['prereqs']['datacenter_name'],
                    template['prereqs']['folder_name'],
                    template['prereqs']['datastore_name'])
             # Get the identifiers of the resources used for deployment
        item_id = helper.get_item_id_by_name(template['vm']['template_name'])

        # Build the deployment specification
        placement_spec = VmtxLibraryItem.DeployPlacementSpec(
                                folder=id_holder.folder,
                                resource_pool=id_holder.resource_pool)
        vm_home_storage_spec = VmtxLibraryItem.DeploySpecVmHomeStorage(datastore=id_holder.datastore)
        disk_storage_spec = VmtxLibraryItem.DeploySpecDiskStorage(datastore=id_holder.datastore)
        deploy_spec = VmtxLibraryItem.DeploySpec(
                                name=template['vm']['vm_name'],
                                placement=placement_spec,
                                vm_home_storage=vm_home_storage_spec,
                                disk_storage=disk_storage_spec)

        # Deploy a virtual machine from the VM template item
        vm_id = client.vmtx_service.deploy(item_id, deploy_spec)
        vm = get_obj_by_moId(servicemanager.content,[vim.VirtualMachine], vm_id)
        print("Deployed VM '{0}' with ID: {1}".format(vm.name,vm_id))

        # Print a summary of the deployed VM
        vm_summary = vm.summary.config
        print('Guest OS: {0}'.format(vm_summary.guestId))
        print('{0} CPU(s)'.format(vm_summary.numCpu))
        print('{0} MB memory'.format(vm_summary.memorySizeMB))
        print('{0} disk(s)'.format(vm_summary.numVirtualDisks))
        print('{0} network adapter(s)'.format(vm_summary.numEthernetCards))

        if turn_on:
             power_on(vsphere_client,template['vm']['vm_name'])
        return vm
             
        

def main():
    # uses what is set in .env file to define these global variables
    esx_ip = config('VCENTER_IP')
    user = config('VCENTER_USER')
    pwd = config('VCENTER_PASS')
    vm_template = 'vm_template.yaml'
    vcenter_conf = 'vcenter.conf'

    #initiates connection to vcenter, leave this as template
    session = requests.session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    client = create_vsphere_client(server=esx_ip, username=user, password=pwd, session=session)

    #change whatever you want to do down here
    



if __name__ == '__main__':
    main()