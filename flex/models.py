from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import RawHTMLBlock
from wagtail.core.fields import StreamField
from wagtail.core.models import Page

from streams import blocks


class FlexPage(Page):
    """Flexibile page class"""

    template = "flex/flex_page.html"
    # content = StreamField()
    subtitle = models.CharField(max_length=100, null=True, blank=True)
    # extra_js = RawHTMLBlock()
    # extra_css = RawHTMLBlock()
    content = StreamField(
        [
            ("html", RawHTMLBlock()),
            ("title_and_text", blocks.TitleAndTextBlock()),
            ("full_richtext", blocks.RichtextBlock()),
            ("simple_richtext", blocks.SimpleRichtextBlock()),
        ],
        null=True,
        blank=True,
    )
    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        # FieldPanel("extra_js"),
        # FieldPanel("extra_css"),
        StreamFieldPanel("content"),
    ]

    class Meta:  # noqa
        verbose_name = "Flex Page"
        verbose_name_plural = "Flex Pages"
