from datetime import datetime
import hmac
try:
    import sha as sha1
except:
    from hashlib import sha1
import base64
import urllib2, urllib
from xml.dom import minidom

class ForbiddenException(Exception):
    pass

def _convert(val):
    if isinstance(val, basestring):
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except:
            pass
    return val

class NodeTraverser(object):
    def __init__(self, node):
        self.node = node

    def keys(self):
        return self.node._attrs.keys()
    def children_keys(self):
        result = []
        for child in self.node.childNodes:
            result.append(child.tagName)
        return result

    @property
    def children(self):
        return [NodeTraverser(n) for n in self.node.childNodes]

    def getattribute(self, name):
        return self.node.getAttribute(name)
        
    def getnode(self, name):
        for child in self.node.childNodes:
            if child.tagName == name:
                return NodeTraverser(child)

    def __getattr__(self, name):
        if type(name) == int or name.isdigit():
            return self.children[int(name)]
        if self.node.hasAttribute(name):
            return self.getattribute(name)
        return self.getnode(name)
    __getitem__ = __getattr__
    @property
    def val(self):
        if self.node.nodeType == self.node.TEXT_NODE:
            return _convert(self.node.data)
        for node in self.node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                return _convert(node.wholeText)
        return None
        
    def __unicode__(self):
        return "<%s>%s</%s>" % (self.node.tagName, self.val, self.node.tagName)
    __str__ = __unicode__
    __repr__ = __str__
        
    def html(self):
        return self.node.toxml()

class XMLWrapper(object):
    def __init__(self, xml):
        self.xml = xml
        self.dom = minidom.parseString(xml)
        setattr(self, self.dom.documentElement.tagName, NodeTraverser(self.dom.documentElement))

class Level3Service(object):
    """
    Parameters :
        key_id(required)
        secret(required)
        service_url : optional that defaults to https://mediaportal.level3.com:443
        content_type : optional that defaults to text/xml
        resource : optional that defaults to /api/v1.0
        method : optional that defaults to GET
        wrap : optional that defaults to True. Will wrap the results in a friendly 
            class that allows you to easily retrieve the values from the xml(see example).
    
    Example Usages:
    
    >>> from level3 import Level3Service
    >>> service = Level3Service('<key id>', '<secret>')
    >>> result = service('rtm/<access group>', {'serviceType' : 'caching', 'accessGroupChildren' : 'false', 'geo' : 'none' })
    >>> result.accessGroup.missPerSecond.val
    50.67
    >>> result.accessGroup.metros[0].name
    Atlanta, GA
    >>> result.accessGroup.metros[0].region
    North America
    >>> result.accessGroup.metros[0].requestsPerSecond.val
    600.45
    """
    
    def __init__(self, key_id, secret, 
      service_url="https://mediaportal.level3.com:443", 
      content_type='text/xml', resource="/api/v1.0", method="GET",
      wrap=True):
        self.key_id = key_id
        self.secret = secret
        self.service_url = service_url
        self.content_type = content_type
        self.resource = resource
        self.method = method
        
        self.current_date = datetime.utcnow()
        self.wrap = wrap
        
    def gen_new_date(self):
        self.current_date = datetime.utcnow()

    @property
    def formatted_date(self):
        return self.current_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
    def generate_auth_string(self, method):
        authstring = "%s\n%s/%s/%s\n%s\n%s\n" % (
            self.formatted_date,
            self.service_url.rstrip('/'),
            self.resource.strip('/'),
            method.strip('/'),
            self.content_type,
            self.method
        )
        
        hash = hmac.new(self.secret, authstring, sha1).digest()
        return "MPA %s:%s" % (self.key_id, base64.b64encode(hash))
        
    def __call__(self, method, options={}, post_data=None):
        self.gen_new_date()
        url = self.service_url.rstrip('/') + '/' + self.resource.strip('/')
        url = url + '/' + method.strip('/')
        
        if options:
            encoded = urllib.urlencode(options)
            url += '?' + encoded
        
        headers = {
            'Date' : self.formatted_date,
            'Authorization' : self.generate_auth_string(method),
            'Content-Type' : self.content_type
        }
        
        req = urllib2.Request(url, headers=headers)
        
        if post_data:
            req.add_data(post_data)        
        
        try:
            result = urllib2.urlopen(req)
        except urllib2.HTTPError, ex:
            if ex.getcode() == 403:
                raise ForbiddenException("something went wrong authorizing this request. %s" % str(ex.readlines()))
            else:
                raise Exception("There was an erorr %s" % str(ex.readlines()))
        data = result.read()
        if self.wrap:
            data = XMLWrapper(data)
        return data