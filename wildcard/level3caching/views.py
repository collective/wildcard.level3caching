from plone.app.form import base as ploneformbase
from zope.formlib import form
from wildcard.level3caching.interfaces import ILevel3CachingSettings
import zope.event
from Products.Five import BrowserView
from wildcard.level3caching.events import on_change
from events import Level3CachePurgeForcedEvent
from zope.event import notify


class Level3SettingsForm(ploneformbase.EditForm):
    form_fields = form.FormFields(ILevel3CachingSettings)

    label = u"Level 3 Caching Settings"
    description = u"Customize the settings used for level3 cache invalidation."

    @form.action(u"Save", condition=form.haveInputWidgets, name=u'save')
    def _handle_save_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data,
                             self.adapters):
            zope.event.notify(ploneformbase.EditSavedEvent(self.context))
            self.status = "Changes saved"
        else:
            zope.event.notify(ploneformbase.EditCancelledEvent(self.context))
            self.status = "No changes"
        self.request.response.redirect(
            self.context.absolute_url() + '/@@level3-settings')


class Utils(BrowserView):

    def invalidate(self):
        on_change(self.context, None, forced=True)
        notify(Level3CachePurgeForcedEvent(self.context, self.request))
        return self.request.response.redirect(
            self.context.absolute_url() + '/view')
