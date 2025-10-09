from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import Membership, Organization

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    org_name = serializers.CharField(required=False, allow_blank=True)
    org_slug = serializers.SlugField(required=False, allow_blank=True)

    def create(self, validated):
        from accounts.models import User
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            first_name=validated.get("first_name",""),
            last_name=validated.get("last_name",""),
        )
        # Si pasa org_name/slug, creamos organización con trial
        org_name = validated.get("org_name")
        org_slug = validated.get("org_slug")
        if org_name and org_slug:
            org = Organization.objects.create(name=org_name, slug=org_slug)
            Membership.objects.create(organization=org, user=user, role="owner")
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs.get("email"), password=attrs.get("password"))
        if not user:
            raise serializers.ValidationError(_("Credenciales inválidas"))
        attrs["user"] = user
        return attrs

class TenantAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extiende el token para incluir:
      - org: {id, slug}
      - roles: roles del usuario en esa org
      - email, uid
    """
    # org_slug llega en el body de login si el usuario tiene varias orgs
    org_slug = serializers.CharField(required=False, allow_blank=True)

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        org_slug = self.initial_data.get("org_slug")

        # Resolver org: si hay slug úsalo, si no la primera membership
        memberships = Membership.objects.select_related("organization").filter(user=self.user)
        current_org = None
        if org_slug:
            current_org = next((m.organization for m in memberships if m.organization.slug == org_slug), None)
        if not current_org and memberships:
            current_org = memberships[0].organization

        # roles en esa org
        roles = []
        if current_org:
            roles = list(memberships.filter(organization=current_org).values_list("role", flat=True))

        # token access con claims
        access = data["access"]
        from rest_framework_simplejwt.tokens import AccessToken
        at = AccessToken(access)
        at["uid"] = str(self.user.id)
        at["email"] = self.user.email
        if current_org:
            at["org"] = {"id": str(current_org.id), "slug": current_org.slug}
            at["roles"] = roles
        data["access"] = str(at)
        return data
