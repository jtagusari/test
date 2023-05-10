"""H-RISK with NoiseModelling plugin init"""

__copyright__ = '(C) 2022 by Junta Tagusari'
__license__ = 'GPL version 3'
__email__ = 'j.tagusari@eng.hokudai.ac.jp'

def classFactory(iface):
    from .hrisk import hrisk_plugin
    return hrisk_plugin(iface)
