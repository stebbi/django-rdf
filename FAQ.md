**What is the current development status?**

Only fit for the brave (or foolhardy :)

**Where is the source code repository?**

At http://code.google.com/p/django-rdf/source/browse.

**Where is the sample code?**

On its way - all the sample code I have is wrapped up in projects I can't distribute, so I need to write some new samples.

**How does Django-RDF compare with other RDF toolkits?**

  * Comparing with [RDFLib](RDFLib.md)
  * Comparing with [Redland](Redland.md)
  * Comparing with [RDFAlchemy](RDFAlchemy.md)

**Why not just use (RDFLib | Redland | RDFAlchemy)**

Django-RDF is intended as an RDF layer on top of the Django ORM. It lets you store data in Django models and construct web pages using views and templates, like you're used to. Then it adds a SPARQL query engine and RDF/XML serialization primitives on top.