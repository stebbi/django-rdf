Mangling is a nifty little tool that let's you map RDF statements to Python object fields.  It gets around a simple issue: A URI is not a valid Python variable name, but a mangled URI is.

Let's take an example. Here is a namespace for Google Code projects, and a resource representing the Django-RDF project:
```
    CODE = create(Namespace, 'code', 'http://code.google.com/p/')
    drdf = create(Resource, CODE, 'django-rdf', get(Namespace, 'code-s')['Project'])
```

The ontology containing the 'Project' concept uses the 'code-s' namespace and belongs to some ontology.

Let's say that ontology also has a predicate called downloads. Each project object has zero or more associated files in its downloads section, and this predicate can represent that sort of relationship.

Then, here is how we might iterate through the downloads for the Django-RDF project:
```
    for download in drdf.CODE_S__downloads:
        ...
```

The field name for the project downloads is derived from the downloads predicate. In a Python shell,
```
>>> ns = get(Namespace, 'code-s')
>>> downloads = ns['downloads']
>>> downloads.mangled
'CODE_S__downloads'
```

The mangling algorithm is simple: just concatenate the mangled namespace code with the predicate name.

The namespace code mangling algorithm is equally simple: cast to upper case and replace dashes with underscores.

Mangling is guaranteed to produce identifiers that are valid Python identifiers, as long as you stick to resource names that are valid Python identifiers.

Mangling produces unique identifers because the resource name is guaranteed to be unique within the namespace, and Django-RDF requires namespace codes to be unique. See notes about [namespace codes](NamespaceCodes.md).