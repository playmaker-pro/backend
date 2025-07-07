import pytest
from django.contrib.auth import get_user_model

from unittest.mock import Mock, patch
from mailing.services import MailingService, TransactionalEmailService
from mailing.schemas import MailContent
User = get_user_model()



class TestMailingService:
    """Test suite for MailingService class."""

    @pytest.fixture
    def mock_mail_content(self):
        """Mock MailContent object."""
        mail_content = Mock(spec=MailContent)
        mail_content.parse_subject.return_value = "Test Subject"
        mail_content.parse_template.return_value = "<h1>Test HTML Body</h1>"
        return mail_content

    @pytest.fixture
    def basic_context(self):
        """Basic context for testing."""
        return {"user": "John Doe", "message": "Welcome!"}

    @pytest.fixture
    def basic_recipients(self):
        """Basic recipients list for testing."""
        return ["user1@example.com", "user2@example.com"]

    @pytest.fixture
    def mailing_service(self, basic_context, basic_recipients, mock_mail_content):
        """Basic MailingService instance."""
        return MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=mock_mail_content,
            sender="sender@example.com",
            email_type="welcome"
        )

    def test_init_with_all_parameters(self, basic_context, basic_recipients, mock_mail_content):
        """Test initialization with all parameters."""
        service = MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=mock_mail_content,
            sender="sender@example.com",
            email_type="welcome"
        )

        assert service.context == basic_context
        assert service.recipients == basic_recipients
        assert service.mail_content == mock_mail_content
        assert service.sender == "sender@example.com"
        assert service.email_type == "welcome"

    def test_init_with_minimal_parameters(self, basic_context, basic_recipients, mock_mail_content):
        """Test initialization with minimal required parameters."""
        service = MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=mock_mail_content
        )

        assert service.context == basic_context
        assert service.recipients == basic_recipients
        assert service.mail_content == mock_mail_content
        assert service.sender is None
        assert service.email_type is None

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    @pytest.mark.django_db
    def test_send_mail_success(self, mock_strip_tags, mock_send_delay, mailing_service):
        """Test successful email sending."""
        # Setup mocks
        mock_strip_tags.return_value = "Test Plain Text Body"

        # Call method
        mailing_service.send_mail()

        # Verify template parsing was called with context
        mailing_service.mail_content.parse_subject.assert_called_once_with(context=mailing_service.context)
        mailing_service.mail_content.parse_template.assert_called_once_with(context=mailing_service.context)

        # Verify strip_tags was called with HTML content
        mock_strip_tags.assert_called_once_with("<h1>Test HTML Body</h1>")

        # Verify send.delay was called with correct parameters
        mock_send_delay.assert_called_once_with(
            subject="Test Subject",
            message="Test Plain Text Body",
            from_email="sender@example.com",
            recipient_list=["user1@example.com", "user2@example.com"],
            html_message="<h1>Test HTML Body</h1>"
        )

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    def test_send_mail_without_sender(self, mock_strip_tags, mock_send_delay, basic_context, basic_recipients,
                                      mock_mail_content):
        """Test sending email without sender specified."""
        service = MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=mock_mail_content
        )
        mock_strip_tags.return_value = "Test Plain Text Body"

        service.send_mail()

        # Verify send.delay was called with None sender
        mock_send_delay.assert_called_once_with(
            subject="Test Subject",
            message="Test Plain Text Body",
            from_email=None,
            recipient_list=basic_recipients,
            html_message="<h1>Test HTML Body</h1>"
        )

    def test_send_mail_without_mail_content(self, basic_context, basic_recipients):
        """Test sending email without mail_content raises ValueError."""
        service = MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=None
        )

        with pytest.raises(ValueError, match="mail_content must be provided"):
            service.send_mail()

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    @patch('mailing.services.UserEmailOutbox.objects.create')
    def test_send_mail_with_email_type_creates_outbox_records(self, mock_create, mock_strip_tags, mock_send_delay,
                                                              mailing_service):
        """Test that outbox records are created when email_type is provided."""
        mock_strip_tags.return_value = "Test Plain Text Body"

        mailing_service.send_mail()

        # Verify outbox records were created for each recipient
        assert mock_create.call_count == 2
        mock_create.assert_any_call(recipient="user1@example.com", email_type="welcome")
        mock_create.assert_any_call(recipient="user2@example.com", email_type="welcome")

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    @patch('mailing.services.UserEmailOutbox.objects.create')
    def test_send_mail_without_email_type_no_outbox_records(self, mock_create, mock_strip_tags, mock_send_delay,
                                                            basic_context, basic_recipients, mock_mail_content):
        """Test that no outbox records are created when email_type is None."""
        service = MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=mock_mail_content,
            sender="sender@example.com"
        )
        mock_strip_tags.return_value = "Test Plain Text Body"

        service.send_mail()

        # Verify no outbox records were created
        mock_create.assert_not_called()

    @patch('mailing.services.UserEmailOutbox.objects.create')
    def test_add_outbox_record_single_recipient(self, mock_create, basic_context, mock_mail_content):
        """Test adding outbox record for single recipient."""
        service = MailingService(
            context=basic_context,
            recipients=["single@example.com"],
            mail_content=mock_mail_content,
            email_type="notification"
        )

        service.add_outbox_record()

        mock_create.assert_called_once_with(recipient="single@example.com", email_type="notification")

    @patch('mailing.services.UserEmailOutbox.objects.create')
    def test_add_outbox_record_multiple_recipients(self, mock_create, mailing_service):
        """Test adding outbox records for multiple recipients."""
        mailing_service.add_outbox_record()

        # Verify outbox records were created for each recipient
        assert mock_create.call_count == 2
        mock_create.assert_any_call(recipient="user1@example.com", email_type="welcome")
        mock_create.assert_any_call(recipient="user2@example.com", email_type="welcome")

    @patch('mailing.services.UserEmailOutbox.objects.create')
    def test_add_outbox_record_empty_recipients(self, mock_create, basic_context, mock_mail_content):
        """Test adding outbox records with empty recipients list."""
        service = MailingService(
            context=basic_context,
            recipients=[],
            mail_content=mock_mail_content,
            email_type="test"
        )

        service.add_outbox_record()

        # Verify no outbox records were created
        mock_create.assert_not_called()

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    def test_send_mail_template_parsing_error(self, mock_strip_tags, mock_send_delay, basic_context, basic_recipients):
        """Test handling of template parsing errors."""
        mail_content = Mock(spec=MailContent)
        mail_content.parse_subject.side_effect = Exception("Template parsing failed")

        service = MailingService(
            context=basic_context,
            recipients=basic_recipients,
            mail_content=mail_content
        )

        with pytest.raises(Exception, match="Template parsing failed"):
            service.send_mail()

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    @patch('mailing.services.UserEmailOutbox.objects.create')
    def test_send_mail_outbox_creation_error(self, mock_create, mock_strip_tags, mock_send_delay, mailing_service):
        """Test handling of outbox creation errors."""
        mock_strip_tags.return_value = "Test Plain Text Body"
        mock_create.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            mailing_service.send_mail()

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    @pytest.mark.django_db
    def test_send_mail_send_task_error(self, mock_strip_tags, mock_send_delay, mailing_service):
        """Test handling of send task errors."""
        mock_strip_tags.return_value = "Test Plain Text Body"
        mock_send_delay.side_effect = Exception("Send task failed")

        with pytest.raises(Exception, match="Send task failed"):
            mailing_service.send_mail()

    @patch('mailing.services.send.delay')
    @patch('mailing.services.strip_tags')
    def test_send_mail_context_passed_correctly(self, mock_strip_tags, mock_send_delay, basic_recipients,
                                                mock_mail_content):
        """Test that context is passed correctly to template methods."""
        custom_context = {"custom_key": "custom_value", "user": "Jane Doe"}
        service = MailingService(
            context=custom_context,
            recipients=basic_recipients,
            mail_content=mock_mail_content
        )
        mock_strip_tags.return_value = "Test Plain Text Body"

        service.send_mail()

        # Verify context was passed to both parsing methods
        mock_mail_content.parse_subject.assert_called_once_with(context=custom_context)
        mock_mail_content.parse_template.assert_called_once_with(context=custom_context)


class TestTransactionalEmailService:
    """Test suite for TransactionalEmailService class."""

    @pytest.fixture
    def test_user(self):
        user, _ = User.objects.get_or_create(
            email="test_user@example.com", username="test_user"
        )
        return user

    @pytest.fixture
    def mock_log(self):
        """Mock log entry object."""
        log = Mock()
        log.id = 456
        log.action = "login"
        log.timestamp = "2023-01-01T10:00:00Z"
        return log

    @pytest.fixture
    def mock_context(self):
        """Mock context dictionary."""
        return {"custom_key": "custom_value", "message": "Test message"}

    @pytest.fixture
    def mock_mail_content(self):
        """Mock mail content object."""
        return Mock()

    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_init_with_all_parameters(self, mock_build_context, test_user, mock_log, mock_context):
        """Test initialization with all parameters."""
        expected_context = {"built": "context"}
        mock_build_context.return_value = expected_context

        service = TransactionalEmailService(
            user=test_user,
            log=mock_log,
            context=mock_context,
            extra_param="extra_value"
        )

        assert service.user == test_user
        assert service.log == mock_log
        assert service.context == expected_context

        # Verify build_email_context was called with correct parameters
        mock_build_context.assert_called_once_with(
            test_user,
            mock_log,
            mock_context,
            extra_param="extra_value"
        )

    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_init_with_minimal_parameters(self, mock_build_context, test_user):
        """Test initialization with minimal required parameters."""
        expected_context = {"built": "context"}
        mock_build_context.return_value = expected_context

        service = TransactionalEmailService(user=test_user)

        assert service.user == test_user
        assert service.log is None
        assert service.context == expected_context

        # Verify build_email_context was called with None values
        mock_build_context.assert_called_once_with(test_user, None, None)

    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_init_with_kwargs(self, mock_build_context, test_user):
        """Test initialization with additional kwargs."""
        expected_context = {"built": "context"}
        mock_build_context.return_value = expected_context

        service = TransactionalEmailService(
            user=test_user,
            custom_param="custom_value",
            another_param=123
        )

        assert service.user == test_user
        assert service.log is None
        assert service.context == expected_context

        # Verify build_email_context was called with kwargs
        mock_build_context.assert_called_once_with(
            test_user,
            None,
            None,
            custom_param="custom_value",
            another_param=123
        )

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_with_custom_recipients(self, mock_build_context, mock_get_template, mock_mailing_service, test_user,
                                         mock_mail_content):
        """Test sending email with custom recipients."""
        # Setup mocks
        mock_build_context.return_value = {"test": "context"}
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_service.return_value = mock_mailing_instance

        custom_recipients = ["custom1@example.com", "custom2@example.com"]

        service = TransactionalEmailService(user=test_user)
        service.send(
            template_key="welcome_email",
            email_type="welcome",
            recipients=custom_recipients
        )

        # Verify EmailTemplateRegistry.get was called
        mock_get_template.assert_called_once_with("welcome_email")

        # Verify MailingService was initialized with correct parameters
        mock_mailing_service.assert_called_once_with(
            context={"test": "context"},
            recipients=custom_recipients,
            email_type="welcome",
            mail_content=mock_mail_content
        )

        # Verify send_mail was called
        mock_mailing_instance.send_mail.assert_called_once()

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_with_default_recipients(self, mock_build_context, mock_get_template, mock_mailing_service, test_user,
                                          mock_mail_content):
        """Test sending email with default recipients (user's contact email)."""
        # Setup mocks
        mock_build_context.return_value = {"test": "context"}
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_service.return_value = mock_mailing_instance

        service = TransactionalEmailService(user=test_user)
        service.send(
            template_key="notification",
            email_type="notification"
        )

        # Verify EmailTemplateRegistry.get was called
        mock_get_template.assert_called_once_with("notification")

        # Verify MailingService was initialized with user's contact email
        mock_mailing_service.assert_called_once_with(
            context={"test": "context"},
            recipients=[test_user.contact_email],
            email_type="notification",
            mail_content=mock_mail_content
        )

        # Verify send_mail was called
        mock_mailing_instance.send_mail.assert_called_once()

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_with_empty_recipients_list(self, mock_build_context, mock_get_template, mock_mailing_service,
                                             test_user, mock_mail_content):
        """Test sending email with empty recipients list defaults to user email."""
        # Setup mocks
        mock_build_context.return_value = {"test": "context"}
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_service.return_value = mock_mailing_instance

        service = TransactionalEmailService(user=test_user)
        service.send(
            template_key="reminder",
            email_type="reminder",
            recipients=[]
        )

        # Verify MailingService was initialized with user's contact email (empty list is falsy)
        mock_mailing_service.assert_called_once_with(
            context={"test": "context"},
            recipients=[test_user.contact_email],
            email_type="reminder",
            mail_content=mock_mail_content
        )

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_template_registry_error(self, mock_build_context, mock_get_template, mock_mailing_service, test_user):
        """Test handling of template registry errors."""
        # Setup mocks
        mock_build_context.return_value = {"test": "context"}
        mock_get_template.side_effect = Exception("Template not found")

        service = TransactionalEmailService(user=test_user)

        with pytest.raises(Exception, match="Template not found"):
            service.send(
                template_key="invalid_template",
                email_type="test"
            )

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_mailing_service_error(self, mock_build_context, mock_get_template, mock_mailing_service, test_user,
                                        mock_mail_content):
        """Test handling of mailing service errors."""
        # Setup mocks
        mock_build_context.return_value = {"test": "context"}
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_instance.send_mail.side_effect = Exception("Mailing failed")
        mock_mailing_service.return_value = mock_mailing_instance

        service = TransactionalEmailService(user=test_user)

        with pytest.raises(Exception, match="Mailing failed"):
            service.send(
                template_key="test_template",
                email_type="test"
            )

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_context_passed_correctly(self, mock_build_context, mock_get_template, mock_mailing_service, test_user,
                                           mock_log, mock_mail_content):
        """Test that context is passed correctly to MailingService."""
        # Setup mocks
        expected_context = {"user_id": 123, "log_action": "login", "custom": "data"}
        mock_build_context.return_value = expected_context
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_service.return_value = mock_mailing_instance

        service = TransactionalEmailService(user=test_user, log=mock_log)
        service.send(
            template_key="action_log",
            email_type="action_notification"
        )

        # Verify MailingService was initialized with the built context
        mock_mailing_service.assert_called_once_with(
            context=expected_context,
            recipients=[test_user.contact_email],
            email_type="action_notification",
            mail_content=mock_mail_content
        )

    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_context_building_with_all_params(self, mock_build_context, test_user, mock_log, mock_context):
        """Test that context building is called with all parameters."""
        mock_build_context.return_value = {"final": "context"}

        service = TransactionalEmailService(
            user=test_user,
            log=mock_log,
            context=mock_context,
            extra_key="extra_value",
            another_param=456
        )

        mock_build_context.assert_called_once_with(
            test_user,
            mock_log,
            mock_context,
            extra_key="extra_value",
            another_param=456
        )

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_send_multiple_calls(self, mock_build_context, mock_get_template, mock_mailing_service, test_user,
                                 mock_mail_content):
        """Test that multiple send calls work correctly."""
        # Setup mocks
        mock_build_context.return_value = {"test": "context"}
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_service.return_value = mock_mailing_instance

        service = TransactionalEmailService(user=test_user)

        # First send
        service.send("template1", "type1", ["recipient1@example.com"])

        # Second send
        service.send("template2", "type2", ["recipient2@example.com"])

        # Verify both calls were made
        assert mock_get_template.call_count == 2
        assert mock_mailing_service.call_count == 2
        assert mock_mailing_instance.send_mail.call_count == 2

        # Verify correct parameters for each call
        mock_get_template.assert_any_call("template1")
        mock_get_template.assert_any_call("template2")

    @patch('mailing.services.MailingService')
    @patch('mailing.services.EmailTemplateRegistry.get')
    @patch('mailing.services.build_email_context')
    @pytest.mark.django_db
    def test_user_without_contact_email(self, mock_build_context, mock_get_template, mock_mailing_service,
                                        mock_mail_content):
        """Test behavior when user doesn't have contact_email attribute."""
        # Setup user without contact_email
        user_without_email = Mock()
        del user_without_email.contact_email  # Remove the attribute

        mock_build_context.return_value = {"test": "context"}
        mock_get_template.return_value = mock_mail_content
        mock_mailing_instance = Mock()
        mock_mailing_service.return_value = mock_mailing_instance

        service = TransactionalEmailService(user=user_without_email)

        # This should raise an AttributeError when trying to access contact_email
        with pytest.raises(AttributeError):
            service.send("template", "type")
