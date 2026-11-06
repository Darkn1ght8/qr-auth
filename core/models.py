from django.db import models


class Metric(models.Model):
    """A data point shown on the testing page (seeded or produced by `benchmark_qr`)."""

    group = models.CharField(max_length=32, db_index=True)
    key = models.CharField(max_length=64)
    label = models.CharField(max_length=128)
    value = models.FloatField()
    unit = models.CharField(max_length=16, blank=True)
    order = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=16, default="seed")  # seed | benchmark | pytest

    class Meta:
        ordering = ["group", "order"]
        unique_together = ("group", "key")
        verbose_name = "Метрика"
        verbose_name_plural = "Метрикалар"

    def __str__(self) -> str:
        return f"{self.group}/{self.key} = {self.value}{self.unit}"
