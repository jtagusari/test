__author__ = 'Junta Tagusari'
__date__ = '2022-12-20'
__copyright__ = '(C) 2022 by Junta Tagusari'

def classFactory(iface):
    from .hrisk import hrisk_plugin
    return hrisk_plugin(iface)
