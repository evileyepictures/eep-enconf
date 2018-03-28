import os
import re
import yaml
from collections import deque, OrderedDict
import logging

log = logging.getLogger(__name__)


def set_logger(logger):
    global log
    log = logger


class EnConf(object):
    """
    This class set environmental variables from YAML file
    All variables defined in oder they were specified.
    So you can use template syntax <ENV_VAR_NAME> to substitute a value

    Here is an example of a configuration file:

    ----------------------------------------------------------------------------
    Global: !omap
        SETTINGS: /Tools/Settings
        SHOWS: /My/Shows/Folder
        PYTHONPATH:
            - <PYTHONPATH>
            - <SETTINGS>/Python/common
            - <SETTINGS>/Python/common/darwin

    Nuke: !omap

        FOUNDRY_LICENSE_FILE: 11111@blaa.eep.com
        foundry_LICENSE: 1111@blaa.eep.com
        NUKE_EEP: <SETTINGS>/nuke/nuke_EEP
        NUKE_PATH:
            - <NUKE_PATH>
            - <NUKE_EEP>/gizmos
    ----------------------------------------------------------------------------

    Note: !omap enforce the dictionary to be in order

    To append value to existing variable:
          VAR1:
             - VAR1
             - VAR2
    """

    def __init__(self):
        # Set !omap constructor to keep dictionary from yaml ordered
        yaml.add_constructor(u'!omap', self.omap_constructor)
        self.config = None

    def omap_constructor(self, loader, node):
        return loader.construct_pairs(node)

    def from_file(self, config_file):
        """
        Read configuration from an YAML file
        :param config_file: (str or pathlib) Path to config file
        """
        with open(str(config_file), 'r') as f:
            self.config = ordered_load(f)
        self.set_env_vars()

    def set_env_vars(self):
        """
        Parse and set all environmental variables
        """

        log.info('-'*79)
        for k, v in self.config.items():
            for i in v:
                name = str(i[0])
                values = i[1]

                if not isinstance(values, list):
                    values = [values]

                queue = deque()
                for value in values:
                    value = os.path.normpath(str(value))

                    # Get template value
                    template_values = re.findall('\<(.*?)\>', value)

                    # This will try to set all of the template values to
                    # their corresponding environmental variable
                    for v in template_values:
                        try:
                            v_val = os.environ[v]
                        except KeyError:
                            v_val = ''
                        value = value.replace('<%s>' % v, v_val)

                    queue.append(value)

                    # assert (value.startswith('\\'))

                # Assemble new path for current env var
                path = ''; cout = 0
                while queue:
                    if cout == 0:
                        path = queue.popleft()
                    else:
                        path = path + os.pathsep + queue.popleft()
                    cout += 1

                # Assign path to current variable
                log.info(name)
                for val in path.split(os.pathsep):
                    log.info('  %s' % val)

                os.environ[name] = path
        log.info('-'*79)

def main():
    """
    Some test functions
    """

    ec = EnConf()
    ec.from_file('./tests/env_test_config.yml')

if __name__ == '__main__':
    main()


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)
