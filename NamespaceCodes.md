XML namespace codes are only required to be unique within individual XML documents.

Django-RDF requires namespace codes to be unique across the entire database because this simplifies [resource name mangling](Mangling.md).

The easiest way to think of this requirement is to consider the entire database to be analogous to a single XML document.