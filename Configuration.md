No modification to any existing code is required, and minimal configuration is necessary - the default behavior is sufficient for most apps, and can be enabled by

  1. Placing the Django-RDF app source directory in the PYTHON\_PATH
  1. Expanding the ontology tarball into the Django-RDF/rdf/ontology/ directory
  1. Adding INSTALLED\_APPS, TEMPLATE\_DIRS and SERIALIZATION\_MODULES entries to settings.py
  1. (Re)Running syncdb to generate the database schema elements for the RDF models
  1. Running the "syncvb" command, to generate an RDF vocabulary from existing models

Syncvb will print a code snippet that can be pasted into settings.py if the SERIALIZATION\_MODULES are missing.