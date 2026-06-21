from django.apps import AppConfig

class ProductsConfig(AppConfig):
    name = 'products'

    def ready(self):
        from rest_framework.serializers import ModelSerializer
        from rest_framework import serializers
        from django.db import models
        
        # Globally map AutoField and BigAutoField to CharField so that MongoDB ObjectIds are serialized as strings
        ModelSerializer.serializer_field_mapping[models.AutoField] = serializers.CharField
        ModelSerializer.serializer_field_mapping[models.BigAutoField] = serializers.CharField
