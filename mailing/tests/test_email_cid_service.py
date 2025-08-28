import os
import tempfile
from unittest.mock import patch

import pytest
from django.core.mail import EmailMultiAlternatives

from mailing.services import EmailCIDService, CIDImageConfig


class TestCIDImageConfig:
    """Test cases for CIDImageConfig class."""

    def test_initialization(self):
        """Test CIDImageConfig initialization."""
        config = CIDImageConfig(
            filename='test.png',
            cid='test_cid',
            path='/path/to/test.png',
            mime_type='image/jpeg'
        )
        
        assert config.filename == 'test.png'
        assert config.cid == 'test_cid'
        assert config.path == '/path/to/test.png'
        assert config.mime_type == 'image/jpeg'

    def test_default_mime_type(self):
        """Test default mime_type is image/png."""
        config = CIDImageConfig(
            filename='test.png',
            cid='test_cid',
            path='/path/to/test.png'
        )
        
        assert config.mime_type == 'image/png'

    def test_exists_method(self):
        """Test exists() method."""
        # Test with non-existent file
        config = CIDImageConfig('test.png', 'cid', '/nonexistent/path.png')
        assert config.exists() is False
        
        # Test with existing file
        with tempfile.NamedTemporaryFile() as temp_file:
            config = CIDImageConfig('test.png', 'cid', temp_file.name)
            assert config.exists() is True


class TestEmailCIDService:
    """Test cases for EmailCIDService."""

    def setup_method(self):
        """Setup for each test method."""
        self.email = EmailMultiAlternatives(
            subject='Test Email',
            body='Test body',
            from_email='test@example.com',
            to=['recipient@example.com']
        )

    @patch('mailing.services.settings')
    def test_get_standard_images(self, mock_settings):
        """Test get_standard_images returns correct configurations."""
        mock_settings.BASE_DIR = '/test/base'
        mock_settings.EMAIL_CID_IMAGES = {
            'header': {
                'filename': 'playmaker_header.png',
                'cid': 'playmaker_header.png',
                'path': 'mailing/images/playmaker_header.png',
                'mime_type': 'image/png',
            },
            'footer': {
                'filename': 'playmaker_footer.png',
                'cid': 'playmaker_footer.png',
                'path': 'mailing/images/playmaker_footer.png',
                'mime_type': 'image/png',
            },
        }
        
        images = EmailCIDService.get_standard_images()
        
        assert len(images) == 2
        assert images[0].filename == 'playmaker_header.png'
        assert images[0].cid == 'playmaker_header.png'
        assert images[1].filename == 'playmaker_footer.png'
        assert images[1].cid == 'playmaker_footer.png'
        
        # Check paths contain expected structure
        for image in images:
            assert 'static/mailing/images' in image.path
            assert image.mime_type == 'image/png'

    def test_attach_image_success(self):
        """Test successful image attachment."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(b'fake_image_data')
            temp_path = temp_file.name
        
        try:
            config = CIDImageConfig(
                filename='test.png',
                cid='test_cid',
                path=temp_path
            )
            
            EmailCIDService.attach_image(self.email, config)
            
            assert len(self.email.attachments) == 1
            attachment = self.email.attachments[0]
            assert attachment.get('Content-ID') == '<test_cid>'
            assert attachment.get('Content-Type') == 'image/png'
            
        finally:
            os.unlink(temp_path)

    def test_attach_image_file_not_exists(self):
        """Test attach_image when file doesn't exist."""
        config = CIDImageConfig(
            filename='missing.png',
            cid='missing_cid',
            path='/nonexistent/path.png'
        )
        
        # Should not raise exception
        EmailCIDService.attach_image(self.email, config)
        
        # No attachments should be added
        assert len(self.email.attachments) == 0

    def test_attach_image_handles_errors(self):
        """Test that file errors are handled gracefully."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            config = CIDImageConfig('test.png', 'test_cid', temp_path)
            
            # Mock file reading to raise an exception
            with patch('builtins.open', side_effect=IOError("Read error")):
                EmailCIDService.attach_image(self.email, config)
            
            # Should handle error gracefully
            assert len(self.email.attachments) == 0
            
        finally:
            os.unlink(temp_path)

    def test_attach_standard_images(self):
        """Test attaching standard images to email."""
        # Create temporary files
        temp_files = []
        try:
            for i in range(2):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(b'fake_image_data')
                temp_files.append(temp_file.name)
                temp_file.close()
            
            # Create mock configs that point to our temp files
            mock_configs = [
                CIDImageConfig(
                    filename='playmaker_header.png',
                    cid='playmaker_header.png',
                    path=temp_files[0]
                ),
                CIDImageConfig(
                    filename='playmaker_footer.png',
                    cid='playmaker_footer.png',
                    path=temp_files[1]
                )
            ]
            
            # Mock get_standard_images to return our configs
            with patch.object(EmailCIDService, 'get_standard_images', return_value=mock_configs):
                EmailCIDService.attach_standard_images(self.email)
                
                # Should attach both images
                assert len(self.email.attachments) == 2
                
                cids = [att.get('Content-ID') for att in self.email.attachments]
                assert '<playmaker_header.png>' in cids
                assert '<playmaker_footer.png>' in cids
                
        finally:
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    @patch('mailing.services.settings')
    def test_attach_standard_images_missing_files(self, mock_settings):
        """Test attach_standard_images when files don't exist."""
        mock_settings.BASE_DIR = '/nonexistent'
        
        # Should not raise exception
        EmailCIDService.attach_standard_images(self.email)
        
        # No attachments should be added
        assert len(self.email.attachments) == 0
