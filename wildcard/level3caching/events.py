from wildcard.level3caching.client import Level3Service
from wildcard.level3caching.settings import Settings
from wildcard.level3caching import runCustomInvalidators
from zope.app.component.hooks import getSite
from Acquisition import aq_parent, aq_inner
from threading import Timer
import logging
logger = logging.getLogger('wildcard.level3caching')


def invalidated_urls(object, base, views):
    urls = []
    if '*' in views:
        for view in views['*'].split('|'):
            urls.append(base + view)
    if object.portal_type in views:
        for view in views[object.portal_type].split('|'):
            urls.append(base + view)
    return urls


def on_change(object, event, forced=False):
    site = getSite()
    settings = Settings(site)
    if not forced and (not settings.auto or not settings.key_id or \
            not settings.secret or not settings.access_group or \
                                            not settings.property_name):
        return

    object = aq_inner(object)
    site_path = '/'.join(site.getPhysicalPath())
    views = settings.invalidated_views
    base = '/'.join(object.getPhysicalPath())[len(site_path):]
    if not forced:
        for path in settings.skipped_paths:
            if base.startswith(path):
                logger.info("skipping invalidation for %s" % base)
                return
    urls = [base]
    base = base + '/'
    urls.append(base)
    urls.extend(invalidated_urls(object, base, views))

    parent = aq_parent(object)
    if getattr(parent, 'default_page', None) == object.getId():
        base = '/'.join(parent.getPhysicalPath())[len(site_path):]
        if base:
            urls.append(base)
        base = base + '/'
        urls.append(base)
        urls.extend(invalidated_urls(parent, base, views))
    urls.extend(runCustomInvalidators(object, parent, site_path, event))

    key_id, secret = settings.key_id, settings.secret
    access_group, property_name = settings.access_group, settings.property_name

    urls = set(urls)
    if '' in urls:
        urls.remove('')

    def do_later():
        try:
            service = Level3Service(key_id, secret, method='POST')
            paths = '\n'.join(['<path>%s</path>' % url for url in urls])
            service('invalidations/%s' % access_group, post_data="""
<properties>
<property>
    <name>%s</name>
    <paths>
        %s
    </paths>
</property>
</properties>
            """ % (property_name, paths)
            )
            logging.info("Invalidating cache for urls %s" % ', '.join(urls))
        except Exception:
            import traceback
            logging.warn(
'There was an error trying to invalidate level(3) cache.\n%s' % (
                traceback.format_exc()))

    # do this in a thread so the page can return promptly
    timer = Timer(0.0, do_later)
    timer.start()


from interfaces import ILevel3CachePurgeForcedEvent
import zope.component.interfaces
from zope.interface import implements


class Level3CachePurgeForcedEvent(zope.component.interfaces.ObjectEvent):
    """An object has been modified"""
    implements(ILevel3CachePurgeForcedEvent)

    def __init__(self, context, request):
        super(Level3CachePurgeForcedEvent, self).__init__(context)
        self.context = context
        self.request = request
