from django.contrib import admin
from django.forms import ModelForm
from django.contrib.auth.admin import UserAdmin

from account.models import User, AccountTier

class UserCreationForm(ModelForm):
    """
    Custom user creation form.
    Without it, accounts created from admin panel have plain text passwords.
    """
    class Meta:
        model = User
        fields = ('username',)

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    """
    Custom admin form.
    """
    add_form = UserCreationForm
    list_display = ("username",)

    fieldsets = (
        (None, {'fields': ('tier', 'username', 'email', 'password', 'first_name', 'last_name')}),
        )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('tier', 'username', 'email', 'password', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active')}
            ),
        )

    filter_horizontal = ()

admin.site.register(User, CustomUserAdmin)
admin.site.register(AccountTier)
