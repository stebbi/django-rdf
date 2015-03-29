Super-condensed...

All the stuff is in svn/trunk/django-rdf. That's the directory you'll want to put on your PYTHONPATH (only the rdf directory will become accessible, because no other directory has an init.py).

In the django-rdf directory,

  * rdf is the reusable Django app
    * management contains the syncvb command
    * managers contains the model managers
    * models is the core
    * ontology is where the ontology files go
    * permissions is just a placeholder
    * query is the SPARQL stuff
    * serializers is the RDF/XML stuff
    * shortcuts has a collection of convenience functions
    * templates is, templates - you know...

  * examples contains a couple of Django projects using rdf
    * auth uses django.contrib.auth
    * simple is good to start with