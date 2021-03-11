#!/bin/bash

public_zhengh3_image_path='/c4site/SOBO/Public/zhengh3/image_bundle'
emc_luob1_upgrade_path='/emc/luob1/jenkins_build'

function finish() {
    echo "[INFO] Reset all root file permissions to current user: $USER"
    local _user=$(id $USER -u)
    local _group=$(id $USER -g)
    cd $WORKSPACE && sudo chown -R ${_user}:${_group} * .*
    echo "[INFO] Reset all root file permissions to current user: $USER [DONE]"
}
trap finish EXIT SIGHUP SIGINT SIGTERM

function die() {
    printf 'ERROR: %s\n' "$@" >&2
    exit 255
}

function catch_error() {
    die "An unhandled error occurred at $BASH_SOURCE:$BASH_LINENO"
}

function get_property() {
    var=$1
    echo "[VAR] $var: ${!var}"
}

function technical_debt() {
    echo "[INFO] git credential approve ..."
    # use same service account for both github and artifactory credentials
    github_hostname=$1
    github_user=$2
    github_password=$3
    artifactory_user=$2
    artifactory_password=$3

    # Cache credentials for a period long enough  (5 days) to perform the import, build and all tests
#   git config --global credential.helper 'cache --timeout 432000' || die "Failed to set credential helper"
    git config credential.helper 'cache --timeout 432000' || die "Failed to set credential helper"

    # Set github credentials
    # TODO: test if Jenkins job already stores github credentials
    echo -e "protocol=https\nhost=${github_hostname}\nusername=${github_user}\npassword=${github_password}\n"
    git credential approve < <(echo -e "protocol=https\nhost=${github_hostname}\nusername=${github_user}\npassword=${github_password}\n") || die "Failed to set credentials for $github_url"

    # Get the Git LFS url, parse it and set credentials for it
    # TODO: could there be more than one LFS repo?
    declare git_lfs_url=$(git config --file .lfsconfig --get lfs.url)
    echo "git_lfs_url: $git_lfs_url"
    [[ $git_lfs_url ]] || die "Failed to obtain Git LFS configuration"

    [[ $git_lfs_url =~ ([^:]*)://([^/]*)/(.*) ]] || die "Failed to parse URL $git_lfs_url"

    echo -e "protocol=${BASH_REMATCH[1]}\nhost=${BASH_REMATCH[2]}\nusername=${artifactory_user}\npassword=${artifactory_password}\n"
    git credential approve < <(echo -e "protocol=${BASH_REMATCH[1]}\nhost=${BASH_REMATCH[2]}\nusername=${artifactory_user}\npassword=${artifactory_password}\n") || die "Failed to set credentials for $url"
}

function clear_zhengh3_image_path()
{
    reserve_builds=4  # total: 5 (old:4 and current one)
    tobe_delete=$(ls -rt ${public_zhengh3_image_path}|head -n -${reserve_builds})
    [ -n "$tobe_delete" ] && (cd $public_zhengh3_image_path; rm -rfv ${tobe_delete})
}

function clear_luob1_upgrade_path()
{
    reserve_builds=4  # total: 5 (old:4 and current one)
    tobe_delete=$(ls -rt ${emc_luob1_upgrade_path}|head -n -${reserve_builds})
    [ -n "$tobe_delete" ] && (cd $emc_luob1_upgrade_path; rm -rfv ${tobe_delete})
}

function archive_image()
{
    if [ "${ARCHIVE_IMAGE:-0}" -ne "1" ]
    then
        echo '[INFO] Skip archive_image'
        return
    fi

    image_root_path='output/image'
    echo "[INFO] Archive images under $image_root_path"
    if [ -d "$image_root_path" ]
    then
        local images=$(find $image_root_path -name "OS-*")
        if [ -n "$images" ]
        then
            clear_zhengh3_image_path
            local today_date=$(date +%F)
            local dst_build_path="${public_zhengh3_image_path}/${today_date}_${BUILD_NUMBER}"
            mkdir -p $dst_build_path
            cp $images $dst_build_path
            CUR_IMAGE=$(find $dst_build_path -name "OS-*")
            echo "[INFO] images saved: $CUR_IMAGE"
        else
            echo "[ERROR] image not found"
        fi
    else
        echo "[ERROR] $image_root_path not found"
    fi
}

function archive_upgrade_package()
{
    if [ "${ARCHIVE_UPGRADE_PACHAGE:-0}" -ne "1" ]
    then
        echo '[INFO] Skip archive_upgrade_package'
        return
    fi

    package_root_path='output/image'
    echo "[INFO] Archive upgrade package under $package_root_path"
    if [ -d $package_root_path ]
    then
        local packages=$(find $package_root_path -name "*.tgz.bin.gpg")
        if [ -n "$packages" ]
        then
            clear_luob1_upgrade_path
            local today_date=$(date +%F)
            local dst_build_path="${emc_luob1_upgrade_path}/${today_date}_${BUILD_NUMBER}"
            mkdir -p $dst_build_path
            cp $packages $dst_build_path
            CUR_IMAGE=$(find $dst_build_path -name "*.tgz.bin.gpg")
            echo "[INFO] upgrade packages saved: $CUR_IMAGE"
        else
            echo "[ERROR] upgrade package not found"
        fi
    else
        echo "[ERROR] $package_root_path not found"
    fi
}

##############################################################
# Main
##############################################################

echo "[INFO] Getting parameters for MergePush Jenkins (github plugin) build"
[[ -n ${GIT_URL} ]] || die "GIT_URL env variable not set by Jenkins job"
[[ -n ${GIT_BRANCH} ]] || die "GIT_BRANCH env variable not set by Jenkins job"
github_url=$(git config --get remote.origin.url)
github_url=${github_url#git@}
github_url=${github_url#http*://}
github_url=${github_url%:*}
declare ci_github_hostname=${github_url%%/*}
declare ci_git_target_branch=${GIT_BRANCH/#origin\//}
declare ci_build_branch=${BUILD_BRANCH:-${ci_git_target_branch}}
declare ci_build_output=${CI_BUILD_OUTPUT_BASE}/${JOB_NAME}/${BUILD_NUMBER}

for prop in GIT_URL GIT_BRANCH ci_github_hostname BUILD_BRANCH ci_build_branch ci_git_target_branch ci_build_output BUILD_CMD
do
    get_property $prop
done

git checkout $ci_build_branch || die "Fail to checkout branch: $ci_build_branch"
head_commit_id=$(git rev-parse HEAD)
echo "[INFO] HEAD: ${head_commit_id} @BRANCH: ${ci_build_branch}"
git log --graph --pretty=format:'%h -%d%s (%cr) <%an>' --abbrev-commit -10
echo ""
[ -e ~/.git-credential-cache/socket ] && rm ~/.git-credential-cache/socket
technical_debt $ci_github_hostname ${USERNAME} ${!USERNAME}
sleep 5
ls -l ~/.git-credential-cache/socket
echo "[RUN] git pull origin $ci_build_branch"
git pull
echo "[RUN] git lfs pull"
git lfs pull
echo -e "###################\n# build_all image #\n###################"
[[ -d $ci_build_output ]] || mkdir -p $ci_build_output
echo "${BUILD_CMD} -C ${WORKSPACE} -i ${BUILD_ITERATOR} -o ${ci_build_output}"
eval "${BUILD_CMD} -C ${WORKSPACE} -i ${BUILD_ITERATOR} -o ${ci_build_output}"

return_code=$?

if [ "$return_code" -eq 0 ]
then
    #echo "ARRAY_NAME=$ARRAY_NAME" |tee ${CI_BUILD_OUTPUT_BASE}/trigger_install_and_upgrade.txt
    echo "IMAGE_PATH=$(find ${CI_BUILD_OUTPUT_BASE}/${JOB_NAME}/${BUILD_NUMBER} -name OS-*)" |tee -a  ${CI_BUILD_OUTPUT_BASE}/trigger_install_and_upgrade.txt
    echo "UPPKG_PATH=$(find ${CI_BUILD_OUTPUT_BASE}/${JOB_NAME}/${BUILD_NUMBER} -name Unity-*gpg)" |tee -a ${CI_BUILD_OUTPUT_BASE}/trigger_install_and_upgrade.txt
else
    cat /dev/null > ${CI_BUILD_OUTPUT_BASE}/trigger_install_and_upgrade.txt
    echo "[INFO] Clear ${CI_BUILD_OUTPUT_BASE}/trigger_install_and_upgrade.txt"
fi

exit $return_code

