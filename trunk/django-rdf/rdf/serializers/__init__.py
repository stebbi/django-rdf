import re, sys, traceback
from xml.etree.cElementTree import ElementTree, iterparse

from django.db.models import Q

from ..models import Namespace, Resource


class _DFacade(object):
    '''
    Facade that wraps a real deserializer. 
    '''

    def __init__(self, delegate, path, **options):
        self._delegate, self.path, self.options = delegate, path, options

    def __iter__(self):
        for o in self._delegate:
            yield o
            
    def __getverbosity(self):
        return self._delegate.verbosity
    def __setverbosity(self, value): 
        self._delegate.verbosity = value
    verbosity = property(__getverbosity, __setverbosity)
    
    def __gettraceback(self):
        return self._delegate.traceback
    def __settraceback(self, value):
        self._delegate.traceback = value
    traceback = property(__gettraceback, __settraceback)
    
    def __getgraceful(self):
        return self._delegate.graceful # IGNORE:W0142
    def __setgraceful(self, value):
        self._delegate.graceful = value # IGNORE:W0142
    graceful = property(__getgraceful, __setgraceful)
    
    
_TAGSPLITTER = re.compile(r'{([^}]*)}(.*)')


def _JC(prefix, suffix):
    '''
    Combines the prefix and suffix argument to form a URI in James Clark notation, 
        {prefix}suffix
    '''
    return u'{%s}%s' % (prefix, suffix) 


def _split_URI(uri, graceful=False):
    '''
    Heuristic attempt at splitting a URI into a namespace and local name. 
    First checks for James Clark notation a la ElementTree.
    Then, looks for a hash (`#`) using rfind and splits on the resulting index, 
    then tries the same with a slash (`/`), 
    then guesses that the URI is actually a qname and attempts to guess the namespace;
    if no attempt works the best guess is that the URI is not namespaced. 
    '''
    try: 
        ns_uri, name = _TAGSPLITTER.findall(uri)[0]
        namespace = Namespace.objects.get(resource__name=ns_uri)
        return namespace, name
    except Exception: # IGNORE:W0703 Catch everything
        pass
    i = uri.rfind('#')
    for sep in (('#', True), ('/', True), (':', False)):
        i = j = uri.rfind(sep[0])
        if -1 == i:
            continue
        if sep[1] is True:
            i = j = i + 1
        else: 
            j += 1
        try: 
            q = Q(resource__name=uri[:i]) | Q(code=uri[:i])
            namespace = Namespace.objects.get(q)
            name = uri[j:]
            return namespace, name
        except Namespace.DoesNotExist: # IGNORE:W0704
            pass
    # The check for a colon is to ensure that misspelled namespace codes are caught
    if graceful is True or -1 == uri.find(':'):
        return None, uri
    exc = sys.exc_info()
    raise exc[0], None, exc[2]


class _DXML(object):
    
    def __init__(self, path, tagmap={}, tagdefault=None, **options): 
        self._path, self._options = path, options
        self._tree = ElementTree()
        self._tree.parse(self._path)
        self.verbosity, self.traceback, self.graceful = 1, False, False
        self._tagmap = tagmap
        self._tagdefault = self._trivial if tagdefault is None else tagdefault
    
    def __iter__(self):
        
        self._preiter_hook()
        
        # Stage 1: namespaces
        for o in self._xml_namespaces(): # IGNORE:E1101
            yield o
            
        # Stage 2: resources
        r = self._tree.getroot() 
        for e in [r] + r.getchildren(): # IGNORE:E1101
            try: 
                for o in self._tagmap.get(e.tag, self._tagdefault)(e):
                    yield o
            except Exception, x: 
                self._except(Exception, x)
                    
        # Stage 3: inheritance etc.
        self._postiter_hook()
    
    def _except(self, cls, x, message=None):
        if 1 < self.verbosity: # IGNORE:E1101
            if message is not None:
                print message
            print x, type(x) 
        if not self.graceful:
            raise x, None, sys.exc_info()[2]
        elif self.traceback: # IGNORE:E1101
            traceback.print_tb(sys.exc_info()[2])
    
    def _preiter_hook(self):
        pass
    
    def _postiter_hook(self):
        pass
    
    def _trivial(self, e):
        _ = e
        for _ in (): yield _
        
    def _xml_namespaces(self):
        for _, e in iterparse(self._path, events=('start-ns',)):
            lcode, uri = e
            if 1 > Namespace.objects.filter(resource__name=uri).count():
                r = Resource(name=uri)
                yield r
                yield Namespace(code=lcode, resource=r)
        
