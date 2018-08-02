from django.db import models



class NewsPiece(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Title",
        blank=True,
        null=True,
    )
    contents = models.TextField(
        verbose_name="News contents",
        max_length=2000,
        blank=True,
        null=True,
    )
    link_url = models.URLField(
        verbose_name="External URL",
        max_length=200,
        blank=True,
        null=True,
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now= True)
