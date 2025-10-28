from rest_framework import serializers
from contacts.models import SupplierNote

class SupplierNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierNote
        fields = ('id','titulo','texto','importante')
