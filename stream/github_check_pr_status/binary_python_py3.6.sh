#!/usr/bin/env bash
set -e
pythonN=python3

temp_dir=$(mktemp -d)
function finish {
  rm -rf "$temp_dir"
}

cur_dir="$PWD"
time=$(date +%s)
python_version=$1
if [ -z "$python_version" ]
then
    python_version=$($pythonN --version 2>&1 | grep -Po '3\.[[:digit:]]+')
fi
declare -r venv_name=${2:-bp}
rm -rf "$cur_dir/$venv_name"

cd "$temp_dir"
virtualenv -p `which $pythonN` $venv_name
virtualenv -p `which $pythonN` --relocatable $venv_name
export VIRTUAL_ENV=${temp_dir}/${venv_name}
export PATH="$VIRTUAL_ENV/bin:$PATH"
unset PYTHON_HOME

pip${python_version} install -r ${cur_dir}/requirements.txt "$cur_dir" --trusted-host=pypi.org
cp ${cur_dir}/* "$temp_dir" -r
#cp "$temp_dir/$venv_name/lib/python${python_version}/site-packages"/* "$temp_dir" -r
#cp "$temp_dir/$venv_name/lib/python${python_version}/site-packages"/.[^.]* "$temp_dir" -r
cd "$temp_dir/$venv_name/lib/python${python_version}/site-packages"
zip -r "${temp_dir}/${venv_name}".zip . >/dev/null
cd "$temp_dir"
rm -rf "$temp_dir/$venv_name"
zip -r "${temp_dir}/${venv_name}".zip . > /dev/null
# Create exectuable zip archive using a shebang and an zip archive
echo '#!/usr/bin/env '"$pythonN" > $venv_name
cat $venv_name.zip >> $venv_name
chmod +x $venv_name
cd "$cur_dir"
mv "$temp_dir/$venv_name" "$cur_dir/$venv_name"
echo "Binary bundle generated: $(readlink -m $cur_dir/$venv_name)"

trap finish EXIT
