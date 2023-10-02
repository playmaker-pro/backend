import json

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager


class TestCreateCourseAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        self.url = reverse("api:profiles:create_course")

    def test_create_course(self) -> None:
        """test create course"""
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "name": "test course",
                    "release_year": 2021,
                }
            ),
            **self.headers
        )

        assert response.status_code == 201

    def test_create_course_with_invalid_release_year(self) -> None:
        """test create course with invalid release year"""
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "name": "test course",
                    "release_year": 1900,
                }
            ),
            **self.headers
        )

        assert response.status_code == 400

    def test_create_course_with_invalid_name(self) -> None:
        """test create course with invalid name"""
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "name": "",
                    "release_year": 2021,
                }
            ),
            **self.headers
        )

        assert response.status_code == 400

    def test_create_course_not_authenticated(self) -> None:
        """test create course not authenticated"""
        response = self.client.post(
            self.url,
            data={
                "name": "test course",
                "release_year": 2021,
            },
        )

        assert response.status_code == 401


class TestUpdateDeleteCourseAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        self.course = factories.CourseFactory(owner=self.user_obj)
        self.url = lambda course_id: reverse(
            "api:profiles:modify_course", kwargs={"course_id": course_id}
        )

    def test_update_course(self) -> None:
        """test update course"""
        response = self.client.patch(
            self.url(self.course.pk),
            data=json.dumps(
                {
                    "name": "test course",
                    "release_year": 2021,
                }
            ),
            **self.headers
        )

        assert response.status_code == 200

    def test_update_course_with_invalid_release_year(self) -> None:
        """test update course with invalid release year"""
        response = self.client.patch(
            self.url(self.course.pk),
            data=json.dumps(
                {
                    "name": "test course",
                    "release_year": 1900,
                }
            ),
            **self.headers
        )

        assert response.status_code == 400

    def test_update_course_with_invalid_name(self) -> None:
        """test update course with invalid name"""
        response = self.client.patch(
            self.url(self.course.pk),
            data=json.dumps(
                {
                    "name": "",
                    "release_year": 2021,
                }
            ),
            **self.headers
        )

        assert response.status_code == 400

    def test_update_course_not_authenticated(self) -> None:
        """test update course not authenticated"""
        response = self.client.patch(
            self.url(self.course.pk),
            data={
                "name": "test course",
                "release_year": 2021,
            },
        )

        assert response.status_code == 401

    def test_update_course_change_owner_id(self) -> None:
        """test update course change owner id"""
        another_user = factories.UserFactory.create()
        response = self.client.patch(
            self.url(self.course.pk),
            data=json.dumps(
                {
                    "owner_id": another_user.pk,
                }
            ),
            **self.headers
        )

        assert response.data["owner"] == self.user_obj.pk

    def test_update_course_for_another_user(self) -> None:
        """test update course for another user"""
        another_user = factories.UserFactory.create()
        another_user_course = factories.CourseFactory(owner=another_user)

        response = self.client.patch(
            self.url(another_user_course.pk), data={"name": "somename"}, **self.headers
        )

        assert response.status_code == 400

    def test_delete_course(self) -> None:
        """test delete course"""
        response = self.client.delete(self.url(self.course.pk), **self.headers)

        assert response.status_code == 204

    def test_delete_course_for_another_user(self) -> None:
        """test delete course for another user"""
        another_user = factories.UserFactory.create()
        another_user_course = factories.CourseFactory(owner=another_user)

        response = self.client.delete(self.url(another_user_course.pk), **self.headers)

        assert response.status_code == 400

    def test_delete_course_not_authenticated(self) -> None:
        """test delete course not authenticated"""
        response = self.client.delete(self.url(self.course.pk))

        assert response.status_code == 401
