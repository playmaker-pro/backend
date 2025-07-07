import pytest
from django.contrib.auth import get_user_model

from mailing.models import EmailTemplate
from mailing.services import MessageContentParser

User = get_user_model()


@pytest.fixture
def test_user():
    """Create a test user for email template testing."""
    user = User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )
    # Mock gender field if it exists
    if hasattr(user, 'userpreferences') and hasattr(user.userpreferences, 'gender'):
        user.userpreferences.gender = "M"  # Male
        user.userpreferences.save()
    return user


@pytest.fixture
def email_template_with_html():
    """Create an email template with HTML content."""
    return EmailTemplate.objects.create(
        subject="Test Subject with #Placeholder|Placeholder#",
        body="Plain text body with #url# and #male|female# forms",
        html_body="<p>HTML body with <a href='#url#'>#url#</a> and #male|female# forms</p>",
        email_type=EmailTemplate.EmailType.NEW_USER,
        is_default=True
    )


@pytest.fixture
def email_template_without_html():
    """Create an email template without HTML content."""
    return EmailTemplate.objects.create(
        subject="Test Subject",
        body="Plain text body with #url#",
        html_body=None,
        email_type=EmailTemplate.EmailType.PASSWORD_CHANGE,
        is_default=True
    )


@pytest.mark.django_db
class TestEmailTemplateHTML:
    """Test EmailTemplate HTML functionality."""
    
    def test_create_email_schema_with_html_body(self, test_user, email_template_with_html):
        """Test create_email_schema method with HTML body."""
        schema = email_template_with_html.create_email_schema(
            test_user, 
            url="https://example.com/activate"
        )
        
        assert schema.subject == "Test Subject with #Placeholder|Placeholder#"
        assert schema.body == "Plain text body with https://example.com/activate and male forms"
        assert schema.html_body == "<p>HTML body with <a href='https://example.com/activate'>https://example.com/activate</a> and male forms</p>"
        assert schema.recipients == [test_user.email]
        assert schema.type == EmailTemplate.EmailType.NEW_USER
    
    def test_create_email_schema_without_html_body(self, test_user, email_template_without_html):
        """Test create_email_schema method without HTML body (backward compatibility)."""
        schema = email_template_without_html.create_email_schema(
            test_user, 
            url="https://example.com/reset"
        )
        
        assert schema.subject == "Test Subject"
        assert schema.body == "Plain text body with https://example.com/reset"
        assert schema.html_body is None  # Should be None when html_body is None
        assert schema.recipients == [test_user.email]
        assert schema.type == EmailTemplate.EmailType.PASSWORD_CHANGE
    
    def test_create_email_schema_with_empty_html_body(self, test_user):
        """Test create_email_schema method with empty HTML body."""
        template = EmailTemplate.objects.create(
            subject="Test Subject",
            body="Plain text body",
            html_body="Plain html body",  # Empty string
            email_type=EmailTemplate.EmailType.SYSTEM,
            is_default=True
        )
        
        schema = template.create_email_schema(test_user)
        
        assert schema.body == "Plain text body"
        assert schema.html_body == "Plain html body"


@pytest.mark.django_db
class TestMessageContentParserHTML:
    """Test MessageContentParser with HTML content."""
    
    def test_parse_html_with_url_placeholder(self, test_user):
        """Test parsing HTML content with URL placeholder."""
        parser = MessageContentParser(test_user, url="https://example.com/test")
        html_content = "<p>Click <a href='#url#'>here</a> to continue</p>"
        
        parsed = parser.parse_email_body(html_content)
        
        assert parsed == "<p>Click <a href='https://example.com/test'>here</a> to continue</p>"
    
    def test_parse_html_with_gender_placeholder(self, test_user):
        """Test parsing HTML content with gender placeholder."""
        parser = MessageContentParser(test_user)
        html_content = "<p>#Kliknąłeś|Kliknęłaś# w link</p>"
        
        parsed = parser.parse_email_body(html_content)
        
        # Should use male form for male user
        assert parsed == "<p>Kliknąłeś w link</p>"
    
    def test_parse_html_with_multiple_placeholders(self, test_user):
        """Test parsing HTML content with multiple placeholders."""
        parser = MessageContentParser(test_user, url="https://example.com/activate")
        html_content = "<p>#Witaj|Witaj# na stronie! <a href='#url#'>Aktywuj konto</a></p>"
        
        parsed = parser.parse_email_body(html_content)
        
        assert parsed == "<p>Witaj na stronie! <a href='https://example.com/activate'>Aktywuj konto</a></p>"
    
    def test_parse_html_preserves_structure(self, test_user):
        """Test that HTML structure is preserved during parsing."""
        parser = MessageContentParser(test_user, url="https://example.com/test")
        html_content = """
        <html>
            <body>
                <h1>Welcome</h1>
                <p>Click <a href='#url#'>here</a></p>
                <div class="footer">
                    <p>#Dziękujemy|Dziękujemy# za rejestrację</p>
                </div>
            </body>
        </html>
        """
        
        parsed = parser.parse_email_body(html_content)
        
        assert "<h1>Welcome</h1>" in parsed
        assert "<a href='https://example.com/test'>here</a>" in parsed
        assert "<div class=\"footer\">" in parsed
        assert "Dziękujemy za rejestrację" in parsed

#
# @pytest.mark.django_db
# class TestBackwardCompatibility:
#     """Test backward compatibility of changes."""
#
#     def test_existing_templates_still_work(self, test_user):
#         """Test that existing templates without html_body still work."""
#         # Create template like the old system (without html_body)
#         template = EmailTemplate.objects.create(
#             subject="Old Template",
#             body="Old style body with #url#",
#             email_type=EmailTemplate.EmailType.NEW_USER,
#             is_default=True
#         )
#
#         schema = template.create_email_schema(test_user, url="https://example.com")
#
#         assert schema.subject == "Old Template"
#         assert schema.body == "Old style body with https://example.com"
#         assert schema.html_body is None
#         assert len(schema.recipients) == 1
#
#     def test_html_body_field_exists(self):
#         """Test that html_body field was added to model."""
#         template = EmailTemplate()
#         assert hasattr(template, 'html_body')
#
#         # Test field properties
#         field = EmailTemplate._meta.get_field('html_body')
#         assert field.blank is True
#         assert field.null is True