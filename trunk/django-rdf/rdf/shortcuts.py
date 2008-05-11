from __future__ import with_statement
from urllib import quote
from random import random


__all__ = ('create', 'get', 'get_or_create', 'create_statements', 'import_class')


def create(*args, **kwargs):
    """
    A shortcut for creating one or more model instances. If one instance is created
    then that instance is returned. If multiple instances are created then they are
    returned in a list.

    To create one instance, the first argument must be the model to use for the
    instance. The remaining arguments are filtered through the 'parameterize' method
    of the model manager before the instance is created using the model manager.

    To create multiple instances, the arguments must be tuples formed as described
    above, with the model to use as the first element of each tuple. The tuples can
    use different models, but any keyword arguments will be passed with every tuple.

    See the parameterize method of the model managers for documentation for the
    remaining arguments required for each model type.
    """
    if isinstance(args[0], tuple):
        return [create(*a, **kwargs) for a in args] # IGNORE:W0142
    return args[0].objects.create(**args[0].objects.parameterize(*args[1:], **kwargs)) # IGNORE:W0142


def get(*args, **kwargs):
    if isinstance(args[0], tuple):
        return [get(*a, **kwargs.copy()) for a in args] # IGNORE:W0142
    return args[0].objects.get(**args[0].objects.parameterize(*args[1:], **kwargs)) # IGNORE:W0142


def get_or_create(*args, **kwargs):
    if isinstance(args[0], tuple):
        return [get_or_create(*a, **kwargs.copy()) for a in args] # IGNORE:W0142
    return args[0].objects.get_or_create(
        **args[0].objects.parameterize(*args[1:], **kwargs)) # IGNORE:W0142


def create_statements(argslist):
    from rdf.models import Statement
    models = []
    for args in argslist:
        kwargs = Statement.objects.parameterize(args)
        models.append(Statement(**kwargs)) # IGNORE:W0142
    saved = []
    for s in models:
        s.save()
        saved.append(s)
    return saved


def import_class(absolutename):
    i = absolutename.rindex('.')
    modulename, classname = absolutename[0:i], absolutename[i+1:]
    module = __import__(modulename, globals(), locals(), (str(classname),))
    return getattr(module, classname)


def render_to_response(*args, **kwargs):
    """
    Shortcut for loading and rendering a template, with RDF namespace dictionary 
    lookups disabled to avoid conflicts with the template engine.
    """
    from django.shortcuts import render_to_response # IGNORE:W0621
    from rdf.models import Namespace
    with Namespace.disabled_dict_lookups():
        content = render_to_response(*args, **kwargs)
    return content


def render_as_resources(**kwargs): # IGNORE:W0613
    """
    Expects the following keyword arguments: 
    
        offset    - offset into a larger resource set, if applicable; or None
        limit     - size of the resource set, if applicable; or None
        format    - defaults to 'xml', can also be 'rdf'
    """
    format = 'rdfxml'
    if kwargs.has_key('format'):
        format = kwargs['format'] 
        del kwargs['format']
    return render_to_response('xml/resources.%s' % format, kwargs)


def urlencode(url):
    return quote(url.encode('utf-8') if type(url) is unicode else url)


def randomized_qname(*segments):
    return urlencode(u''.join(segments + (str(hash(abs(random()))),)))


