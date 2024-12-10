import argparse
import glob
import os
import datetime

from lib.common.logger import getLogger
logger = getLogger(__file__)

IGNORE_FILES = ['.gitkeep']
DATETIME_FORMATTER = '%Y%m%d%H%M%S'
WILD_CARD = '*'

input_path = 'data/input/'
output_path = 'data/output/'

def clean_up(base_path='/', target_dir=input_path):
    p = base_path + target_dir
    for f in os.listdir(base_path+input_path):
        if f in IGNORE_FILES:
            continue
        t = f'{p}/{f}'
        logger.info(f'remove file: {t}')
        os.remove(t)

def datetime_suffix():
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    return datetime.datetime.now(JST).strftime(DATETIME_FORMATTER)

def run(base_path='/', identifier='csv', disable_cleanup=False, disable_override_base_path=False):
    base_path = '/' if disable_override_base_path else base_path
    p = base_path + input_path + WILD_CARD
    files = glob.glob(p)
    for file in files:
        if not file.endswith(identifier):
            continue
        logger.info(f'target file: {file}')
        with open(file, 'r') as input:
            f = base_path + output_path + os.path.splitext(os.path.basename(file))[0] + f'.{datetime_suffix()}.{identifier}'
            logger.info(f'write results to: {f}')
            with open(f, 'w') as output:
                output.write(input.read())
    
    if not disable_cleanup:
        logger.info('enabled force clean up')
        # assumes input data in azure files will be removed
        clean_up(base_path, input_path)

if __name__ == "__main__":
    '''
        When local testing, 
        you should add disable_force_cleanup as commandline args !!!! (otherwise test data will be removed)

        Assumes Input data in AzureFiles as temp data, and will remove after process has finished
    '''

    parser = argparse.ArgumentParser(description='API Server running on AKS Cluster')
    parser.add_argument('--disable_force_cleanup', action='store_true', help='disable if avoid removing input data')
    parser.add_argument('--disable_override_base_path', action='store_true', help='disable if avoid overriding base path')
    args = parser.parse_args()

    base_path = f'{os.path.abspath(os.path.dirname(__file__))}/'
    run(base_path=base_path, identifier='csv', disable_cleanup=args.disable_force_cleanup, disable_override_base_path=args.disable_override_base_path)
