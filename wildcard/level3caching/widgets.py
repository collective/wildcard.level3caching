from zope.interface import implements
from zope.component import getMultiAdapter
from zope.app.form.browser.widget import BrowserWidget
from zope.app.form.interfaces import IDisplayWidget, IInputWidget
from zope.app.form import InputWidget
from zope.app.form.interfaces import WidgetInputError, MissingInputError
from zope.i18n import translate


def DictionaryWidgetFactory(field, request):
    widget = getMultiAdapter((field, field.key_type, field.value_type,
                              request),
                             IInputWidget)
    return widget


class SimpleDictionaryWidget(BrowserWidget, InputWidget):
    """A widget for editing arbitrary dictionaries

        key_editsubwidget - optional edit subwidget for key components
        key_displaysubwidget - optional display subwidget for key components
        value_editsubwidget - optional edit subwidget for value components
    """
    implements(IInputWidget)
    _type = dict

    def __init__(self, context, key_type, value_type, request,
                 key_editsubwidget=None, key_displaysubwidget=None,
                 value_editsubwidget=None):
        super(SimpleDictionaryWidget, self).__init__(context, request)
        self.key_editsubwidget = key_editsubwidget
        self.key_displaysubwidget = key_displaysubwidget
        self.value_editsubwidget = value_editsubwidget
        self.context.key_type.bind(object())
        self.mayadd = True

    def _widgetpostproc(self, widget, key, keyorvalue):
        """For manipulating css classes of given elements"""

    def _sortkeys(self, keys):
        newkeys = [x for x in keys.__iter__()]
        newkeys.sort()
        return newkeys

    def _renderKeyAndCheckBox(self, render, key, i):
        render.append('<input class="editcheck" type="checkbox" '
                      'name="%s.remove_%d" />' % (self.name, i))
        keydisplaywidget = self._getWidget(
            str(i), IDisplayWidget, self.context.key_type,
            self.key_displaysubwidget, 'key-display')
        self._widgetpostproc(keydisplaywidget, key, 'key-display')
        keydisplaywidget.setRenderedValue(key)
        render.append(keydisplaywidget())

    def _renderitems(self, render):
        keys = self._data.keys()
        keys = self._sortkeys(keys)
        for i in range(len(keys)):
            key = keys[i]
            value = self._data[key]
            render.append('<div>')
            render.append('<span>')
            self._renderKeyAndCheckBox(render, key, i)
            keyhiddenwidget = self._getWidget(
                str(i), IInputWidget, self.context.key_type,
                self.key_editsubwidget, 'key')
            keyhiddenwidget.setRenderedValue(key)
            render.append(keyhiddenwidget.hidden())
            render.append('</span>')
            valuewidget = self._getWidget(
                str(i), IInputWidget, self.context.value_type,
                self.value_editsubwidget, 'value')
            self._widgetpostproc(valuewidget, key, 'value-edit')
            valuewidget.setRenderedValue(value)
            render.append('<span>' + valuewidget() + '</span></div>')

    def _renderbuttons(self, render):
        buttons = ''
        if (len(self._data) > 0) and len(self._data) > self.context.min_length:
            button_label = u"Remove selected items"
            button_label = translate(button_label, context=self.request,
                                     default=button_label)
            buttons += ('<input type="submit" '
                        'value="%s" name="%s.remove"/>' % (button_label,
                                                           self.name))
        if (self.context.max_length is None or
                len(self._data) < self.context.max_length) and self.mayadd:
            field = self.context.value_type
            button_label = u'Add %s'
            button_label = translate(button_label, context=self.request,
                                     default=button_label)
            button_label = button_label % (field.title or field.__name__)
            buttons += '<input type="submit" ' + \
                       'name="%s.add" value="%s" />' % (self.name,
                                                        button_label)
            self._keypreproc()
            newkeywidget = self._getWidget(
                'new', IInputWidget, self.context.key_type,
                self.key_editsubwidget, 'key')
            self._keypostproc()
            self._widgetpostproc(newkeywidget, '', 'key-edit')
            render.append('<div><span>%s</span></div>' % (newkeywidget(),))
        if buttons:
            render.append('<div><span>%s</span></div>' % buttons)

    def __call__(self):
        """Render the Widget"""
        assert self.context.key_type is not None
        assert self.context.value_type is not None
        render = []
        render.append('<div><div id="%s">' % (self.name,))
        if not self._getRenderedValue():
            if self.context.default is not None:
                self._data = self.context.default
            else:
                self._data = self._type()

        self._renderitems(render)

        render.append('</div>')
        # possibly generate the "remove" and "add" buttons
        self._renderbuttons(render)

        render.append(self._getPresenceMarker(len(self._data)))
        render.append('</div>')
        text = "\n".join(render)
        return text

    def _getWidget(self, i, interface, value_type, customwidget, mode):
        if customwidget is not None:
            widget = getMultiAdapter((value_type, self.request),
                                     interface,
                                     name=self.customwidget)
        else:
            widget = getMultiAdapter((value_type, self.request), interface)
        widget.setPrefix('%s.%s.%s.' % (self.name, i, mode))
        return widget

    def hidden(self):
        self._getRenderedValue()
        keys = self._data.keys()
        parts = [self._getPresenceMarker(len(self._data))]

        for i in range(len(keys)):
            key = keys[i]
            # value = self._data[key]
            keywidget = self._getWidget(
                str(i), IInputWidget, self.context.key_type,
                self.key_displaysubwidget, 'key')
            keywidget.setRenderedValue(key)
            valuewidget = self._getWidget(
                str(i), IInputWidget, self.context.value_type,
                self.value_editsubwidget, 'value')
            parts.append(keywidget.hidden() + valuewidget.hidden())

        return "\n".join(parts)

    def _getPresenceMarker(self, count=0):
        return ('<input type="hidden" name="%s.count" value="%d" />' % (
            self.name, count))

    def _getRenderedValue(self):
        if not self._renderedValueSet():
            if self.hasInput():
                self._data = self._generateDict()
            else:
                self._data = {}
        if self._data is None:
            self._data = self._type()
        if len(self._data) < self.context.min_length:
            """Don't know, what to do here :-("""
        return self._data

    def getInputValue(self):
        if self.hasInput():
            dict = self._type(self._generateDict())
            for key, val in dict.items():
                if not val:
                    del dict[key]
            if dict != self.context.missing_value:
                self.context.validate(dict)
            elif self.context.required:
                raise MissingInputError(self.context.__name__,
                                        self.context.title)
            return dict
        raise MissingInputError(self.context.__name__, self.context.title)

    def applyChanges(self, content):
        field = self.context
        value = self.getInputValue()
        change = field.query(content, self) != value
        if change:
            field.set(content, value)
        return change

    def hasInput(self):
        return (self.name+".count") in self.request.form

    def _generateDict(self):
        # len_prefix = len(self.name)
        adding = False
        # removing = []
        if self.context.value_type is None:
            return []

        try:
            count = int(self.request.form[self.name + ".count"])
        except ValueError:
            raise WidgetInputError(self.context.__name__, self.context.title)

        keys = {}
        values = {}
        for i in range(count):
            remove_key = "%s.remove_%d" % (self.name, i)
            if remove_key not in self.request.form:
                keywidget = self._getWidget(
                    str(i), IInputWidget, self.context.key_type,
                    self.key_displaysubwidget, 'key')
                valuewidget = self._getWidget(
                    str(i), IInputWidget, self.context.value_type,
                    self.value_editsubwidget, 'value')
                keys[i] = keywidget.getInputValue()
                try:
                    values[i] = valuewidget.getInputValue()
                except:
                    values[i] = ''
        adding = (self.name+".add") in self.request.form

        mykeys = keys.items()
        mykeys.sort()
        dict = {}
        for (i, key) in mykeys:
            dict[key] = values[i]

        if adding:
            newkeywidget = self._getWidget(
                'new', IInputWidget, self.context.key_type,
                self.key_displaysubwidget, 'key')
            newkey = newkeywidget.getInputValue()
            self.context.key_type.validate(newkey)
            if newkey not in dict:
                dict[newkey] = ''

        return dict

    def _keypreproc(self):
        """Only for subclassing"""

    def _keypostproc(self):
        """Only for Subclassing"""
