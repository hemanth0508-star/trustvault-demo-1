from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountFlowTests(TestCase):
    def test_registration_creates_account_without_signing_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new_vault_user",
                "email": "new@example.com",
                "password1": "A-Strong-Password-938!",
                "password2": "A-Strong-Password-938!",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTrue(User.objects.filter(username="new_vault_user").exists())

    def test_logout_requires_post_and_ends_session(self):
        user = User.objects.create_user(
            username="logout_user",
            password="A-Strong-Password-938!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.pk,
        )

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_home_links_to_vault_not_registration(self):
        user = User.objects.create_user(
            username="home_user",
            password="A-Strong-Password-938!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("document_list"))
        self.assertNotContains(response, reverse("register"))

    def test_signed_in_user_is_not_sent_to_the_account_creation_form(self):
        user = User.objects.create_user(
            username="already_registered",
            password="A-Strong-Password-938!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("register"))

        self.assertRedirects(
            response,
            reverse("home"),
            fetch_redirect_response=False,
        )
        home_response = self.client.get(response.url)
        self.assertContains(home_response, "You are already signed in")
        self.assertContains(home_response, reverse("document_list"))
