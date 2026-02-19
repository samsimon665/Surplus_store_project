from allauth.account.models import EmailAddress


def is_email_verified(user):
    return EmailAddress.objects.filter(
        user=user,
        verified=True
    ).exists()
