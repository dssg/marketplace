from allauth.account import views as allauth_views
from django.urls import path, re_path

urlpatterns = [
    path("confirm-email/",
         allauth_views.EmailVerificationSentView.as_view(template_name='marketplace/verification_sent.html'),
         name="account_email_verification_sent"),

    re_path(r"^confirm-email/(?P<key>[-:\w]+)/$",
            allauth_views.ConfirmEmailView.as_view(template_name='marketplace/email_confirm.html'),
            name="account_confirm_email"),
]
