#!/bin/bash
function die() {
    printf 'ERROR: %s\n' "$@" >&2
    exit 255
}

MLUSANITY_P=${CI_BUILD_OUTPUT_BASE}/${JOB_NAME}/${BUILD_NUMBER}
MluSanity_path='safe/catmerge/layered/MLU/test/Sanity/OffArraySanity'
if [ -d "${MluSanity_path}" ]
then
    [ -n "${MLUSANITY_P}" ] || die "Sanity materials not found"
    [ -d "${MLUSANITY_P}" ] || mkdir -p ${MLUSANITY_P} || die "Could not create '${MLUSANITY_P}'"
    [ -e "${MLUSANITY_P}/OffArraySanity.tar.gz" ] && rm -f "${MLUSANITY_P}/OffArraySanity.tar.gz"
    tar zcf ${MLUSANITY_P}/OffArraySanity.tar.gz ${MluSanity_path}\
    binaries/OffArraySanity-tools/unzip.exe\
    binaries/OffArraySanity-tools/pslist.exe\
    binaries/OffArraySanity-tools/psexec.exe\
    binaries/OffArraySanity-tools/plink.exe\
    binaries/OffArraySanity-tools/ktcons.exe\
    binaries/OffArraySanity-tools/killsp.exe\
    binaries/OffArraySanity-tools/IOXStatus.exe\
    binaries/OffArraySanity-tools/IOXSizer.exe\
    binaries/OffArraySanity-tools/IOXipclog.exe\
    binaries/OffArraySanity-tools/IOX.exe\
    binaries/OffArraySanity-tools/IOXDoIO.exe\
    binaries/OffArraySanity-tools/dotnetfx35setup.exe\
    binaries/OffArraySanity-tools/BlockXCopy.exe\
    binaries/OffArraySanity-tools/Axsizer.exe\
    binaries/OffArraySanity-tools/Axkill.exe\
    binaries/OffArraySanity-tools/ArrayxMT.exe\
    binaries/misc/msvc/killsp.pdb\
    binaries/misc/libraries/tldlib_4.dll\
    binaries/misc/libraries/msvcr71.dll\
    binaries/misc/libraries/msvcr71d.dll\
    binaries/misc/libraries/mp_engine.dll\
    binaries/misc/libraries/killsp.lib\
    binaries/misc/executables/ndmpcopy\
    binaries/misc/executables/Linux_x86_64_vjtree\
    binaries/misc/executables/Linux_i386_vjtree || die "CMD 'tar zcf ${MLUSANITY_P}/OffArraySanity.tar.gz ${MluSanity_path}' failed"
    ls -lh ${MLUSANITY_P}/OffArraySanity.tar.gz
else
    die "'${MluSanity_path}' not found"
fi
