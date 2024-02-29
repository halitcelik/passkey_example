from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from ..forms.auth import UserLoginForm, UserLoginOptionsForm
from passkeys.models import UserPasskey


def login_view(request):
    next_ = request.GET.get("next", request.POST.get("next", "/"))
    button_text = _("Suivant")
    template = "auth/login.html"
    use_passkeys = "passkeys" in settings.INSTALLED_APPS

    if hasattr(request, "htmx") and request.htmx:
        template = "auth/includes/login-form.html"
    if request.method == "POST":
        if request.POST.get("password"):
            form = UserLoginForm(request.POST)
            if form.is_valid():
                form.login_user(request)
                return HttpResponseRedirect(
                    request.GET.get("next", form.cleaned_data.get("next", "/"))
                )
        else:
            if use_passkeys:
                user_passkey = UserPasskey.objects.filter(
                    user__email=request.POST.get("email"), enabled=True
                ).first()
                if user_passkey is not None:
                    auth_options = {}

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
