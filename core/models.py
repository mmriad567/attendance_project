from django.db import models


class SystemSetting(models.Model):
    """Small key/value store for institute-level configuration."""

    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("key",)

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, description=""):
        obj, _ = cls.objects.update_or_create(
            key=key, defaults={"value": value, "description": description}
        )
        return obj
