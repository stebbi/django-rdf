from django.contrib.auth.models import ContentType, Permission


def _permission_code(instance, suffix):
    return u':'.join((instance.code, suffix))

def _permission_name(instance, prefix):
    return u' '.join((prefix, instance.title))


CODES_AND_NAMES = (('r', 'Read'), ('w', 'Write'), ('x', 'Execute'))


def update_RDF_permissions(instance):
    # Get the Django content type for the Concept model, 
    # then create a permission name that uniquely identifies the type and the action - 
    ct = ContentType.objects.get(
        app_label=instance._meta.app_label, model=instance._meta.object_name.lower()) # IGNORE:W0212
    for code, name in CODES_AND_NAMES:
        _update_RDF_permission(instance, ct, code, name)

def _update_RDF_permission(instance, content_type, code_suffix, name_prefix):
    code = _permission_code(instance, code_suffix)
    try: 
        _ = Permission.objects.get(content_type=content_type, codename=code) # IGNORE:E1101
    except Permission.DoesNotExist: # IGNORE:E1101
        name = _permission_name(instance, name_prefix)
        Permission.objects.create(content_type=content_type, codename=code, name=name) # IGNORE:E1101


def update_namespace_permissions(instance):
    update_RDF_permissions(instance)
    

def update_type_permissions(instance):
    update_RDF_permissions(instance)
    

def update_predicate_permissions(instance):
    update_RDF_permissions(instance)

