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

# Delete Block DS
#echo "Step1:Delete Block DS"
#(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds -id $block_ds_1 delete)
#(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds -id $block_ds_2 delete)
#(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds -id $block_ds_3 delete)


## Delete File DS

#echo "Step2:Delete File DS"
#(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds -id $file_ds_1 delete)
#(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds -id $file_ds_2 delete)
#(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/prov/vmware/vvolds -id $file_ds_3 delete)

#echo "Step3:Delete capability profile"

#read -s -n1 -p "press any key to continue" val
#echo -e "\n"

# Delete NASSERVER
echo "============================================================================="
echo "Step4:Delete NASSERVER"
echo "============================================================================="
read pe_id < temp/pe_id.txt
read nas_if_id < temp/nas_if_id.txt
read nas_id < temp/nas_id.txt
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/vmwarepe -id $pe_id delete)
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/if -id $nas_if_id delete)
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/nas/server -id $nas_id delete)

# Delete vCenter and ESXi Host
echo "============================================================================="
echo "Step5:Delete vCenter and ESXi Host"
echo "============================================================================="
read vc_id < temp/vc_id.txt
read host_id < temp/host_id.txt
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /virt/vmw/vc -id $vc_id delete)
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d 10.245.82.144 /remote/host -id $host_id delete)

# Delete pool and iscsi inf
echo "============================================================================="
echo "Step6:Delete pool and iscsi interface"
echo "============================================================================="
read if_id1 < temp/if_id1.txt
read if_id2 < temp/if_id2.txt
read pool_id < temp/pool_id.txt
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/if -id $if_id1 delete)
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /net/if -id $if_id2 delete)
(set -x; uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $mgmt_ip /stor/config/pool -id $pool_id delete)
