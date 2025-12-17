from django.shortcuts import redirect


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("adminpanel:login")

        # Logged in but NOT using admin session → ask to login as admin
        if not request.user.is_superuser or not request.session.get("is_admin"):
            return redirect("adminpanel:login")

        return view_func(request, *args, **kwargs)

    return wrapper
