from rest_framework import serializers
from contacts.models import ClientAttachment
class ClientAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientAttachment
        fields = ('id','categoria','file','nombre_original','confidencial','sha256')
        read_only_fields = ('sha256',)
