from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Apply monkeypatching for Django built-in and third party models
        # to ensure they use MongoDB-compatible ObjectIdAutoField for primary keys.
        from django_mongodb_backend.fields import ObjectIdAutoField

        def patch_model_to_mongodb_id(model):
            if not hasattr(model, 'id'):
                return
            old_id = model._meta.get_field('id')
            if old_id.__class__.__name__ == 'ObjectIdAutoField':
                return
            new_id = ObjectIdAutoField(primary_key=True, serialize=False)
            
            # Remove old field references from model metadata
            model._meta.local_fields = [f for f in model._meta.local_fields if f.name != 'id']
            model._meta.auto_field = None
            if hasattr(model._meta, '_field_cache'):
                delattr(model._meta, '_field_cache')
                
            # Re-contribute the field as ObjectIdAutoField
            new_id.contribute_to_class(model, 'id')
            model._meta.pk = new_id

        # Target built-in Django models
        from django.contrib.admin.models import LogEntry
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType

        patch_model_to_mongodb_id(LogEntry)
        patch_model_to_mongodb_id(Group)
        patch_model_to_mongodb_id(Permission)
        patch_model_to_mongodb_id(ContentType)

        # Target third party simplejwt token_blacklist models if installed
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            patch_model_to_mongodb_id(OutstandingToken)
            patch_model_to_mongodb_id(BlacklistedToken)
        except ImportError:
            pass
