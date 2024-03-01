import json
from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from ..forms.auth import UserLoginForm, UserLoginOptionsForm
from passkeys.models import UserPasskey
from passkeys.backend import PasskeyBackendException
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.urls import reverse
from passkeys.FIDO2 import getServer, getUserCredentials, enable_json_mapping
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from fido2.utils import websafe_encode, websafe_decode
from passkeys.FIDO2 import auth_complete
from django.contrib.auth import login


def login_view(request):
    next_ = request.GET.get("next", request.POST.get("next", "/"))
    button_text = _("Suivant")
    template = "auth/login.html"
    use_passkeys = "passkeys" in settings.INSTALLED_APPS
    auth_data = {}
    if hasattr(request, "htmx") and request.htmx:
        template = "auth/includes/login-form.html"
    if request.method == "POST":
        form = UserLoginForm(request.POST)
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
                            Pas de compte? <a href='{reverse("auth.signup")}'>S'inscrire</a>"""
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

                enable_json_mapping()
                User = get_user_model()
                credentials = getUserCredentials(request.POST.get(User.USERNAME_FIELD))
                server = getServer(request)
                user_passkey = UserPasskey.objects.filter(
                    user__email=request.POST.get("email"), enabled=True
                ).first()

                if user_passkey is not None:
                    auth_data, state = server.authenticate_begin(credentials)
                    auth_data = dict(auth_data)
                    request.session["fido2_state"] = state
            button_text = _("Connexion")
            form = UserLoginForm(
                initial={"next": next_, "email": request.POST.get("email")}
            )
    else:
        form = UserLoginOptionsForm(initial={"next": next_})

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
    return render(
        request,
        "auth/signup.html",
        {
            "use_passkeys": "passkeys" in settings.INSTALLED_APPS,
        },
    )


class PasswordResetView(DjangoPasswordResetView):
    form_class = PasswordResetForm
