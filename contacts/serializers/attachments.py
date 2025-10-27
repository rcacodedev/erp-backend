from rest_framework import serializers
from contacts.models import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ("id","nombre_original","tipo_mime","tamano_bytes","file","sha256",
                  "categoria","confidencial","antivirus_estado","periodo_nomina")
        read_only_fields = ("sha256","antivirus_estado")

    def validate(self, attrs):
        cat = attrs.get('categoria') or getattr(self.instance, 'categoria', None)
        per = attrs.get('periodo_nomina') or getattr(self.instance, 'periodo_nomina', None)
        if cat == 'nomina' and not per:
            raise serializers.ValidationError({"periodo_nomina":"Obligatorio cuando categoria='nomina' (YYYY-MM-01)."})
        return attrs
