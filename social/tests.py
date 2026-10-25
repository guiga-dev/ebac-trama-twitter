from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase,APIClient
from rest_framework.authtoken.models import Token
from .models import Profile,Tweet,Follow,Like,Comment
import tempfile
from pathlib import Path

@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    STORAGES={"default":{"BACKEND":"django.core.files.storage.FileSystemStorage"},"staticfiles":{"BACKEND":"django.contrib.staticfiles.storage.StaticFilesStorage"}},
)
class SocialAPITests(APITestCase):
    def setUp(self):
        self.alice=get_user_model().objects.create_user(username="alice",password="Only-testing-strong-421!")
        self.bob=get_user_model().objects.create_user(username="bob",password="Only-testing-strong-422!")
        self.carol=get_user_model().objects.create_user(username="carol",password="Only-testing-strong-423!")
        for user in (self.alice,self.bob,self.carol):Profile.objects.create(user=user)
        self.tweet=Tweet.objects.create(author=self.bob,body="Ideias sobre Django")

    def test_registration_hashes_password_and_creates_profile(self):
        response=self.client.post("/api/auth/register/",{"username":"diana","password":"Strong-testing-password-549!"})
        self.assertEqual(response.status_code,201,response.data)
        user=get_user_model().objects.get(username="diana")
        self.assertTrue(user.check_password("Strong-testing-password-549!"))
        self.assertNotEqual(user.password,"Strong-testing-password-549!")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_weak_password_and_duplicate_username_rejected(self):
        self.assertEqual(self.client.post("/api/auth/register/",{"username":"new","password":"123"}).status_code,400)
        self.assertEqual(self.client.post("/api/auth/register/",{"username":"alice","password":"Strong-testing-346!"}).status_code,400)

    def test_login_logout_and_wrong_password(self):
        self.assertEqual(self.client.post("/api/auth/login/",{"username":"alice","password":"incorrect"}).status_code,400)
        self.assertEqual(self.client.post("/api/auth/login/",{"username":"alice","password":"Only-testing-strong-421!"}).status_code,200)
        self.assertEqual(self.client.get("/api/me/").data["username"],"alice")
        self.assertEqual(self.client.post("/api/auth/logout/").status_code,204)
        self.assertIn(self.client.get("/api/me/").status_code,(401,403))

    def test_csrf_is_required_for_login_and_registration(self):
        client=APIClient(enforce_csrf_checks=True)
        client.get("/")
        self.assertIn("csrftoken",client.cookies)
        self.assertEqual(client.post("/api/auth/login/",{"username":"alice","password":"Only-testing-strong-421!"}).status_code,403)
        self.assertEqual(client.post("/api/auth/register/",{"username":"new","password":"Strong-testing-346!"}).status_code,403)
        self.assertEqual(client.post("/api/auth/login/",{"username":"alice","password":"Only-testing-strong-421!"},HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code,200)

    def test_partial_profile_update_does_not_require_other_fields(self):
        self.client.force_authenticate(self.alice)
        self.alice.profile.bio="Bio preservada";self.alice.profile.save()
        response=self.client.patch("/api/me/",{"display_name":"Alice Dev"})
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data["display_name"],"Alice Dev")
        self.assertEqual(response.data["bio"],"Bio preservada")
        self.assertEqual(self.client.patch("/api/me/",{}).status_code,200)

    def test_avatar_upload_and_download(self):
        self.client.force_authenticate(self.alice)
        stream=BytesIO();Image.new("RGB",(16,16),(10,90,60)).save(stream,format="PNG")
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent.parent) as directory,override_settings(MEDIA_ROOT=directory):
            response=self.client.patch("/api/me/",{"avatar":SimpleUploadedFile("avatar.png",stream.getvalue(),content_type="image/png")},format="multipart")
            self.assertEqual(response.status_code,200,response.data)
            self.assertEqual(self.client.get(response.data["avatar"]).status_code,200)
            self.assertEqual(self.client.patch("/api/me/",{"display_name":"Novo"}).status_code,200)
            self.assertTrue(self.client.get("/api/me/").data["avatar"])

    def test_invalid_avatar_rejected(self):
        self.client.force_authenticate(self.alice)
        response=self.client.patch("/api/me/",{"avatar":SimpleUploadedFile("bad.png",b"not-image",content_type="image/png")},format="multipart")
        self.assertEqual(response.status_code,400)

    def test_password_change_requires_old_password_and_invalidates_token(self):
        self.client.force_authenticate(self.alice)
        Token.objects.create(user=self.alice)
        self.assertEqual(self.client.post("/api/me/password/",{"old_password":"wrong","new_password":"Changed-password-426!"}).status_code,400)
        self.assertEqual(self.client.post("/api/me/password/",{"old_password":"Only-testing-strong-421!","new_password":"123"}).status_code,400)
        response=self.client.post("/api/me/password/",{"old_password":"Only-testing-strong-421!","new_password":"Changed-password-426!"})
        self.assertEqual(response.status_code,200,response.data)
        self.alice.refresh_from_db();self.assertTrue(self.alice.check_password("Changed-password-426!"))
        self.assertFalse(Token.objects.filter(user=self.alice).exists())

    def test_follow_is_idempotent_and_self_follow_rejected(self):
        self.client.force_authenticate(self.alice)
        for _ in range(2):self.assertEqual(self.client.post(f"/api/users/{self.bob.pk}/follow/").status_code,200)
        self.assertEqual(Follow.objects.count(),1)
        self.assertEqual(self.client.post(f"/api/users/{self.alice.pk}/follow/").status_code,400)
        self.assertEqual(self.client.delete(f"/api/users/{self.bob.pk}/follow/").status_code,200)
        self.assertEqual(Follow.objects.count(),0)

    def test_followers_and_following_lists(self):
        Follow.objects.create(follower=self.alice,followed=self.bob)
        self.assertEqual(self.client.get(f"/api/users/{self.bob.pk}/followers/").data["results"][0]["id"],self.alice.pk)
        self.assertEqual(self.client.get(f"/api/users/{self.alice.pk}/following/").data["results"][0]["id"],self.bob.pk)

    def test_feed_only_contains_followed_users(self):
        Tweet.objects.create(author=self.alice,body="Meu próprio tweet")
        Tweet.objects.create(author=self.carol,body="Pessoa não seguida")
        Follow.objects.create(follower=self.alice,followed=self.bob)
        self.client.force_authenticate(self.alice)
        response=self.client.get("/api/tweets/feed/")
        self.assertEqual([t["id"] for t in response.data["results"]],[self.tweet.pk])

    def test_empty_following_has_empty_feed(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.get("/api/tweets/feed/").data["results"],[])

    def test_tweet_crud_and_ownership(self):
        self.client.force_authenticate(self.alice)
        response=self.client.post("/api/tweets/",{"body":"Minha ideia","author":self.bob.pk})
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(response.data["author"]["id"],self.alice.pk)
        url=f"/api/tweets/{response.data['id']}/"
        self.assertEqual(self.client.patch(url,{"body":"Atualizado"}).status_code,200)
        self.assertEqual(self.client.patch(f"/api/tweets/{self.tweet.pk}/",{"body":"Invasão"}).status_code,403)
        self.assertEqual(self.client.delete(f"/api/tweets/{self.tweet.pk}/").status_code,403)
        self.assertEqual(self.client.delete(url).status_code,204)

    def test_tweet_validation_and_anonymous_access(self):
        self.assertEqual(self.client.get("/api/tweets/").status_code,200)
        self.assertIn(self.client.post("/api/tweets/",{"body":"Anônimo"}).status_code,(401,403))
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.post("/api/tweets/",{"body":" "}).status_code,400)
        self.assertEqual(self.client.post("/api/tweets/",{"body":"a"*281}).status_code,400)

    def test_likes_idempotent_and_unlike(self):
        self.client.force_authenticate(self.alice)
        url=f"/api/tweets/{self.tweet.pk}/like/"
        for _ in range(2):
            response=self.client.post(url)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data["likes_count"],1)
        self.assertEqual(Like.objects.count(),1)
        self.assertEqual(self.client.delete(url).data["likes_count"],0)

    def test_comment_create_read_delete_and_ownership(self):
        self.client.force_authenticate(self.alice)
        response=self.client.post(f"/api/tweets/{self.tweet.pk}/comments/",{"body":"Boa ideia!"})
        self.assertEqual(response.status_code,201,response.data)
        comment_id=response.data["id"]
        self.assertEqual(self.client.get(f"/api/tweets/{self.tweet.pk}/comments/").data["count"],1)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.delete(f"/api/comments/{comment_id}/").status_code,403)
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.delete(f"/api/comments/{comment_id}/").status_code,204)

    def test_list_pagination_and_profile_filter(self):
        Tweet.objects.bulk_create([Tweet(author=self.alice,body=f"Ideia {n}") for n in range(25)])
        data=self.client.get(f"/api/tweets/?author={self.alice.pk}").data
        self.assertEqual(data["count"],25)
        self.assertEqual(len(data["results"]),20)
        self.assertIsNotNone(data["next"])

    def test_search_profiles(self):
        response=self.client.get("/api/users/?search=ali")
        self.assertEqual([u["username"] for u in response.data["results"]],["alice"])

    def test_frontend_template_and_static_references(self):
        response=self.client.get("/")
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"Trama")
        self.assertContains(response,"social/app.js")
        self.assertContains(response,"social/app.css")
