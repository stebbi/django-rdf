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


# Copyright (c) 2008, Stefan B Sigurdsson
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice, 
#        this list of conditions and the following disclaimer.
#     
#     2. Redistributions in binary form must reproduce the above copyright 
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
# 
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
