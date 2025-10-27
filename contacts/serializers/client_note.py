from rest_framework import serializers
from contacts.models import ClientNote
class ClientNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientNote
        fields = ('id','titulo','texto','importante')
