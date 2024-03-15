from passkeys.backend import PasskeyBackendException
from passkeys.FIDO2 import auth_complete
from passkeys.models import UserPasskey

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..forms.auth import (
    LoginOptionsForm,
    PasskeyLoginForm,
    PasswordLoginForm,
    SignupForm,
)


def login_view(request):
    next_ = request.GET.get("next", request.POST.get("next", "/"))
    button_text = _("Suivant")
    template = "auth/login.html"
    use_passkeys = "passkeys" in settings.INSTALLED_APPS
    auth_data = {}
    if hasattr(request, "htmx") and request.htmx:
        template = "auth/includes/login-form.html"
    if request.method == "POST":
        form = PasswordLoginForm(request.POST)
        if request.POST.get("password"):
            try:
                if form.is_valid():
                    form.login_user(request)
                    return HttpResponseRedirect(
                        request.GET.get("next", form.cleaned_data.get("next", "/"))
                    )
            except PasskeyBackendException:
                form.add_error(
                    field=None,
                    error=ValidationError(
                        mark_safe(
                            f"""
                            Adresse email ou mot de passe erronée.
                            Pas de compte?
                            <a href='{reverse("auth.signup")}'>S'inscrire</a>"""
                        )
                    ),
                )

        else:
            if use_passkeys:
                passkey = request.POST.get("passkeys")
                if passkey:
                    user = auth_complete(request)
                    if user:
                        login(
                            request,
                            user,
                            backend=[
                                be
                                for be in settings.AUTHENTICATION_BACKENDS
                                if "PasskeyModelBackend" in be
                            ][0],
                        )
                        return HttpResponseRedirect(next_)

                user_passkey = UserPasskey.objects.filter(
                    user__email=request.POST.get("email"), enabled=True
                ).first()

                if user_passkey is not None:
                    request.session["base_username"] = request.POST.get("email")
                    form = PasskeyLoginForm(
                        initial={"next": next_, "email": request.POST.get("email")}
                    )
                else:
                    form = PasswordLoginForm(
                        initial={"next": next_, "email": request.POST.get("email")}
                    )
            button_text = _("Connexion")

    else:
        form = LoginOptionsForm(initial={"next": next_})

    return render(
        request,
        template,
        {
            "form": form,
            "next": next_,
            "page_title_override": _("Connexion"),
            "button_text": button_text,
            "current_page": "auth.login",
            "use_passkeys": use_passkeys,
            "auth_data": auth_data,
        },
    )


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")


def signup_view(request):
    form = SignupForm()
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("passkeys:login"))
    return render(
        request,
        "auth/signup.html",
        {
            "use_passkeys": "passkeys" in settings.INSTALLED_APPS,
            "form": form,
        },
    )


class PasswordResetView(DjangoPasswordResetView):
    form_class = PasswordResetForm
