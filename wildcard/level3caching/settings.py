from zope.interface import implements
from persistent.dict import PersistentDict
from zope.annotation.interfaces import IAnnotations
from wildcard.level3caching.interfaces import ILevel3CachingSettings

class Settings(object):
    implements(ILevel3CachingSettings)
    
    def __init__(self, context):
        self.context = context
        annotations = IAnnotations(self.context)

        self._metadata = annotations.get('wildcard.level3caching', None)
        if self._metadata is None:
            self._metadata = PersistentDict()
            annotations['wildcard.level3caching'] = self._metadata
                    
    def __setattr__(self, name, value):
        if name[0] == '_' or name in ['context']:
            self.__dict__[name] = value
        else:
            self._metadata[name] = value

    def __getattr__(self, name):
        default = None
        if name in ILevel3CachingSettings.names():
            default = ILevel3CachingSettings[name].default

        return self._metadata.get(name, default)