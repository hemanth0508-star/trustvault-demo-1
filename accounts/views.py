from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import RegistrationForm
def register(request):
    if request.user.is_authenticated:
        return redirect("document_list")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your account was created successfully. Please log in."
            )

            return redirect("login")
    else:
        form = RegistrationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form},
    )