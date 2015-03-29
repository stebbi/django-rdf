Django-RDF is an RDF engine implemented in a generic, reusable Django app, providing complete RDF support to Django projects without requiring any modifications to existing framework or app source code, or incurring any performance penalty on existing control flow paths.

The philosophy is simple: Do your web development using Django just like you're used to, then turn the knob and - with no additional effort - expose your project on the semantic web.

The project home is at Google Code and there is also a Google Group to help coordinate.

  * http://code.google.com/p/django-rdf
  * http://groups.google.com/group/django-rdf

**Features**

Django-RDF can expose models from any other app as RDF data. This makes it easy to write new views that return RDF/XML data, and/or query existing models in terms of RDFS or OWL classes and properties using (a variant of) the SPARQL query language. SPARQL in, RDF/XML out - two basic semantic web necessities.

Django-RDF also implements an RDF store using its internal models such as Concept, Predicate, Resource, Statement, Literal, Ontology, Namespace, etc. The SPARQL query engine returns query sets that can freely mix data in the RDF store with data from existing Django models.

**Internals**

During [configuration](Configuration.md), the syncvb command inspects the database schema created by running syncdb and generates OWL ontologies for other apps in INSTALLED\_APPS. The ontologies are serialized to RDF/XML files in the django-rdf/ontology/ directory, and subsequenty deserialized to create a combined vocabulary in the form of RDF model instances.

The RDFS/OWL classes and properties in the vocabulary are associated with elements of the database schema that are then used by the SPARQL compiler to generate SQL code. A SPARQLQuerySet implementation wraps the compiler and provides access to model instances or values using the familiar Django query set interface - filter, count, iteration with slices, etc.

A set of APIs gives convenient access to resources. Here is a toy example of a view that uses django.contrib.auth, resets the first name of a user and then renders everything known about that user in the RDF/XML format:
```
def reset_first_name(request, username, first_name):
    AUTH = Namespace.objects.get(code='auth') 
    # Returns a django.contrib.auth.models.User object: 
    user = AUTH['user#%s' % username]
    # Resets the first name of the user:
    Statement.objects.create(user, AUTH['User__first_name'], first_name)
    # Renders everything known about the user in RDF/XML format:
    return render_as_rdf({resources: (user,)})
```

A small set of shortcuts, templates and template tags simplifies RDF/XML output. An RDF/XML serializer/deserializer is also included.

**Plan**

Django-RDF was initially implemented in March 2008. Current status as of April 25 2008 is as follows:

  * RDF store, basic SPARQL compiler and query set, render\_as\_rdf shortcut, RDF/XML deserializer, syncvb command are functional.

  * URI synthesis for instances of existing models needs a rewrite.
  * SPARQL implementation is missing features.
  * SPARQL syntax is not compatible with the W3C Recommendation.
  * No access control yet.
  * No internationalization yet.
  * No samples yet.
  * ... and there are many other rough edges here and there.

The plan is to have a fairly polished "ready-for-release" version sometime in summer 2008. A fairly extensive set of unit tests already exists but there is still a lot of churn in various parts of the API, and the immediate goal is to extend the test coverage until the API reaches a more stable state. Feedback from the first intrepid users will be greatly appreciated! (And much of it will likely sound something like, hey, that's not working quite as advertised! :)

Enjoy,

Stefán

