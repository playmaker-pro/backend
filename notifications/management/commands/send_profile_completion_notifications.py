from django.core.management.base import BaseCommand

from notifications.services import ProfileCompletionNotificationService


class Command(BaseCommand):
    """
    Custom management command to trigger the sending of notifications related to incomplete profile data.

    This command runs a series of checks to identify users with specific pieces of missing profile information
    and sends them reminders to complete their profiles. The notifications cover various aspects such as
    location, alternative player positions, favorite formations, agency data, external links, videos, photos,
    and certifications/courses.

    The command is designed to be run as a scheduled task, ensuring regular checks and updates to the users.
    It utilizes the ProfileCompletionNotificationService to handle the logic for determining which notifications
    to send and to whom.
    """
    help = 'Send notifications for incomplete profile data'

    def handle(self, *args, **kwargs):
        service = ProfileCompletionNotificationService()

        try:
            service.check_and_notify_for_missing_location()
            service.check_and_notify_for_missing_alternative_position()
            service.check_and_notify_for_missing_favorite_formation()
            service.check_and_notify_for_incomplete_agency_data()
            service.check_and_notify_for_missing_external_links()
            service.check_and_notify_for_missing_video()
            service.check_and_notify_for_missing_photo()
            service.check_and_notify_for_missing_certificate_course()

            self.stdout.write(self.style.SUCCESS('Successfully sent all notifications'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error occurred: {e}'))
