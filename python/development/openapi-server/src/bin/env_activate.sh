#!/bin/bash

# This file must be used with "source bin/activate" *from bash*

# https://qiita.com/yudoufu/items/48cb6fb71e5b498b2532
ROOT_PATH=$(dirname $(dirname $(cd $(dirname ${BASH_SOURCE[0]:-$0}); pwd)))
AKS_BASE_PATH=$(dirname $(cd $(dirname ${BASH_SOURCE[0]:-$0}); pwd))

add_env_path()
{
    eval "v=\$$1"
    if [ "$v" != "" ]; then
        # e.g. PYTHONPATH=$PYTHONPATH:$NEW_PATH
        eval "export ${1}=\$${1}:\${2}"
    else
        eval "export ${1}=\${2}"
    fi
}

activate_aksvenv()
{
    local p
    unameout="$(uname -s)"
    case "${unameout}" in
        Linux*)
            p="bin";;
        *)
            p="Scripts";;
    esac

    if [ ! -d $ROOT_PATH/.aksenv ]; then
        python -m venv $ROOT_PATH/.aksenv


        . $ROOT_PATH/.aksenv/${p}/activate

        python -m pip install --upgrade pip
        pip install -r $ROOT_PATH/requirements.txt
    else
        . $ROOT_PATH/.aksenv/${p}/activate
    fi
}

deactivate_aksvenv()
{
    unset ROOT_PATH
    unset AKS_BASE_PATH

    unset add_env_path
    unset activate_aksvenv

    # 必要に応じて追加していく
    unset PYTHONPATH

    # venv の activate によって source される関数
    deactivate
}

activate_aksvenv
add_env_path PYTHONPATH $AKS_BASE_PATH