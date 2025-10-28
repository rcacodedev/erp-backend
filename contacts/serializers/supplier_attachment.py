from rest_framework import serializers
from contacts.models import SupplierAttachment

class SupplierAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAttachment
        fields = ('id','categoria','file','nombre_original','confidencial','sha256')
        read_only_fields = ('sha256',)
