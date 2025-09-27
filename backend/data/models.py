from django.db import models

class Item(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    marketHashName = models.CharField(max_length=255)
    BUFF = models.CharField(max_length=100)
    C5 = models.CharField(max_length=100)
    HALOSKINS = models.CharField(max_length=100)
    YOUPIN = models.CharField(max_length=100)

    class Meta:
        db_table = 'items'
        managed = False

class KlineDataHour(models.Model):
    timestamp = models.BigIntegerField(primary_key=True)
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    turnover = models.DecimalField(max_digits=15, decimal_places=2)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kline_data_hour'
        managed = False

class KlineDataDay(models.Model):
    timestamp = models.BigIntegerField(primary_key=True)
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    turnover = models.DecimalField(max_digits=15, decimal_places=2)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kline_data_day'
        managed = False

class KlineDataWeek(models.Model):
    timestamp = models.BigIntegerField(primary_key=True)
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    turnover = models.DecimalField(max_digits=15, decimal_places=2)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kline_data_week'
        managed = False
