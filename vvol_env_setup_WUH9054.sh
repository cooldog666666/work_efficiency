#!/bin/bash
set -e
mgmt_ip='10.245.82.144'

vcenter='10.244.126.187'
esx_host='10.244.126.133'

port_1='spa_iom_1_eth0'
port_2='spb_iom_1_eth0'
port_3='spa_ocp_0_eth0'
port_4='spb_ocp_0_eth0'

ioip_1='10.245.191.171'
ioip_2='10.245.191.172'
ioip_3='10.245.191.173'
ioip_4='10.245.191.174'

gateway='10.245.191.1'
netmask='255.255.255.0'
res1=
function uemcli_record()
{
    echo "$1"
    res=`$1`
    echo "$res"
    res1=`echo $res|awk 'NR==1{print $3}'`
}
mkdir -p temp
# Create pool and iscsi inf
echo "============================================================================="
echo "Step1:Create pool and iscsi interface"
echo "============================================================================="
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/config/pool create -name vvol_pool -storProfile profile_12 -drivesNumber 10 -diskGroup dg_3"
pool_id=$res1
echo "$pool_id" > temp/pool_id.txt
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/if create -type iscsi -port $port_1 -ipv4 static -addr $ioip_1 -netmask $netmask -gateway $gateway"
if_id1=$res1
echo "$if_id1" > temp/if_id1.txt
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/if create -type iscsi -port $port_2 -ipv4 static -addr $ioip_2 -netmask $netmask -gateway $gateway"
if_id2=$res1
echo "$if_id2" > temp/if_id2.txt

# Add vCenter and ESXi Host
echo "============================================================================="
echo "Step2:Add vCenter and ESXi Host"
echo "============================================================================="
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /virt/vmw/vc create -addr $vcenter -username administrator@vsphere.local -passwd Password123! -registerVasaProvider yes -localUsername admin -localPasswd Password123!"
vc_id=$res1
echo "$vc_id" > temp/vc_id.txt
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /virt/vmw/esx create -addr $esx_host -vc $vc_id"
host_id=$res1
echo "$host_id" > temp/host_id.txt
# Create NASSERVER
echo "============================================================================="
echo "Step3:Create NASSERVER"
echo "============================================================================="
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/server create -name nasserver -sp spa -pool $pool_id -enableNFS yes"
nas_id=$res1
echo "$nas_id" > temp/nas_id.txt
nfs_id=`echo  "$nas_id"  | grep -P "\d+" -o`
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/if create -server $nas_id -port $port_3 -addr $ioip_3 -netmask $netmask -gateway $gateway"
nas_if_id=$res1
echo "$nas_if_id" > temp/nas_if_id.txt
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/nfs -id nfs_$nfs_id set -v4 yes)
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/vmwarepe create -server $nas_id -if $nas_if_id"
pe_id=$res1
echo "$pe_id" > temp/pe_id.txt
exit
echo "Step4"
echo "============================================================================="
echo "# Please make sure there are already capability profile created like this:"
echo "# cp_1:Compression_And_Dedup, cp_2:Compression_Only, cp_3:Compression_Off."
#echo "# Please cancel this execution in 3 mins if the 3 cp are not ready in storage."
#sleep 180
read -s -n1 -p "press any key to continue" val
echo -e "\n"

# Create Block DS
echo "Step5:Create Block DS"
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds create -name Block_DS_Compression_And_Dedup -cp cp_4,cp_6 -size 200G,200G -type block -hosts $host_id"
block_ds_1=$res1
export block_ds_1
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds create -name Block_DS_Compression_Only -cp cp_5,cp_6 -size 200G,200G -type block -hosts $host_id"
block_ds_2=$res1
export block_ds_2
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds create -name Block_DS_Compression_Off -cp cp_6 -size 200G -type block -hosts $host_id"
block_ds_3=$res1
export block_ds_3


## Create File DS

echo "Step6:Create File DS"

uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds create -name File_DS_Compression_And_Dedup -cp cp_4,cp_6 -size 200G,200G -type file -hosts $host_id"
file_ds_1=$res1
export file_ds_1
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds create -name File_DS_Compression_Only -cp cp_5,cp_6 -size 200G,200G -type file -hosts $host_id"
file_ds_2=$res1
export file_ds_2
uemcli_record "uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds create -name File_DS_Compression_Off -cp cp_6 -size 200G -type file -hosts $host_id"
file_ds_3=$res1
export file_ds_3
