from zope.interface import Interface
from zope import schema

class ILayer(Interface):
    """
    layer class
    """
    
class ILevel3CachingSettings(Interface):
    auto = schema.Bool(title=u"Automatically Invalidate", default=False)
    key_id = schema.TextLine(title=u'Key ID')
    secret = schema.TextLine(title=u'Secret')
    access_group = schema.TextLine(title=u'Access Group')
    property_name = schema.TextLine(title=u'Property Name')

    skipped_paths = schema.List(
        title=u"Skipped Paths",
        description=u"Specify Paths that are excluded from automatic invalidation. These should be absolute paths with the root being the Plone site.",
        default=[],
        missing_value=[],
        value_type=schema.TextLine(title=u"path"),
    )
    
    invalidated_views = schema.Dict(
        title=u"Views to Invalidate",
        description=u"Map portal_types to view names. '*' for any portal type.",
        key_type=schema.TextLine(title=u'Portal type'),
        value_type=schema.TextLine(title=u'portal type', description=u"comma seperated"),
        missing_value={},
        default={
            '*' : 'view',
            'Folder' : 'rss.xml|atom.xml|RSS',
            'Large Plone Folder' : 'rss.xml|atom.xml|RSS',
            'News Item' : ''
        }
    )


class ILevel3CachePurgeForcedEvent(Interface):
    """
    """