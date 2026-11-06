from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Электрондық пошта", required=False)
    first_name = forms.CharField(label="Аты", max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "email")
        labels = {"username": "Логин"}
        help_texts = {"username": "Латын әріптері, сандар және @/./+/-/_ таңбалары."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Құпиясөз"
        self.fields["password1"].help_text = "Кемінде 8 таңба, тек сандардан тұрмауы керек."
        self.fields["password2"].label = "Құпиясөзді қайталаңыз"
        self.fields["password2"].help_text = ""
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "field__input")
            field.widget.attrs.setdefault("autocomplete", {
                "username": "username",
                "email": "email",
                "first_name": "given-name",
                "password1": "new-password",
                "password2": "new-password",
            }.get(name, "off"))


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Логин немесе құпиясөз қате. Қайта тексеріп көріңіз.",
        "inactive": "Бұл аккаунт бұғатталған.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["password"].label = "Құпиясөз"
        self.fields["username"].widget.attrs.update({"class": "field__input", "autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"class": "field__input", "autocomplete": "current-password"})
