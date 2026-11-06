import os

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm, UserCreationForm

from core.i18n import t, t_lazy

User = get_user_model()

RESERVED_USERNAMES = {"admin", "administrator", "root", "superuser", "staff"}


def _style(form, autocomplete: dict) -> None:
    for name, field in form.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            continue
        field.widget.attrs.setdefault("class", "field__input")
        field.widget.attrs.setdefault("autocomplete", autocomplete.get(name, "off"))


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label=t_lazy("Электронная почта"), required=True)
    first_name = forms.CharField(label=t_lazy("Имя"), max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = t("Логин")
        self.fields["username"].help_text = t("Латинские буквы, цифры и символы @/./+/-/_.")
        self.fields["password1"].label = t("Пароль")
        self.fields["password1"].help_text = t("Минимум 8 символов, не только цифры.")
        self.fields["password2"].label = t("Повторите пароль")
        self.fields["password2"].help_text = ""
        _style(self, {"username": "username", "email": "email", "first_name": "given-name",
                      "password1": "new-password", "password2": "new-password"})

    def clean_username(self):
        username = self.cleaned_data["username"]
        reserved = RESERVED_USERNAMES | {os.environ.get("ADMIN_USERNAME", "admin").lower()}
        if username.lower() in reserved:
            raise forms.ValidationError(t("Этот логин зарезервирован системой. Выберите другой."))
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(t("Эта почта уже зарегистрирована. Войдите или укажите другую."))
        return email


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": t_lazy("Неверный логин или пароль. Проверьте и попробуйте снова."),
        "inactive": t_lazy("Этот аккаунт заблокирован."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = t("Логин")
        self.fields["password"].label = t("Пароль")
        _style(self, {"username": "username", "password": "current-password"})


class ChangePasswordForm(PasswordChangeForm):
    """Logged-in user (or admin) changes their own password."""

    logout_others = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = t("Текущий пароль")
        self.fields["new_password1"].label = t("Новый пароль")
        self.fields["new_password1"].help_text = t("Минимум 8 символов, не только цифры и не похож на логин.")
        self.fields["new_password2"].label = t("Повторите новый пароль")
        self.fields["logout_others"].label = t("Выйти на всех других устройствах")
        self.error_messages = {
            **self.error_messages,
            "password_incorrect": t("Текущий пароль введён неверно."),
            "password_mismatch": t("Пароли не совпадают."),
        }
        _style(self, {"old_password": "current-password", "new_password1": "new-password", "new_password2": "new-password"})


class NewPasswordForm(SetPasswordForm):
    """New password without the old one: reset link, or an admin setting it for a user."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = t("Новый пароль")
        self.fields["new_password1"].help_text = t("Минимум 8 символов, не только цифры и не похож на логин.")
        self.fields["new_password2"].label = t("Повторите новый пароль")
        self.error_messages = {**self.error_messages, "password_mismatch": t("Пароли не совпадают.")}
        _style(self, {"new_password1": "new-password", "new_password2": "new-password"})


class ResetRequestForm(forms.Form):
    email = forms.EmailField(label=t_lazy("Электронная почта"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self, {"email": "email"})

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
