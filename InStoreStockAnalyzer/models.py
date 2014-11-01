from django.db import models

class Department(models.Model):
    i_department = models.AutoField(primary_key=True, verbose_name='Sr. No#')
    iD = models.CharField(
        max_length=256, blank=True, null=True, unique=True)
    name = models.CharField(
        max_length=256, blank=True, null=True)
    category = models.CharField(
        max_length=128, blank=True, null=True)
    browseToken = models.CharField(
        max_length=128, blank=True, null=True)
    parentId = models.CharField(
        max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        
    def __unicode__(self):
        return self.name
        
        
class Products(models.Model):
    i_product = models.AutoField(primary_key=True, verbose_name='Sr. No#')
    i_department = models.ForeignKey(Department)
    iD = models.CharField(
        max_length=128, blank=True, null=True)
    name = models.CharField(
        max_length=256, blank=True, null=True)
    upc = models.CharField(
        max_length=128, blank=True, null=True)    
    walmart_availability = models.CharField(
        max_length=128, blank=True, null=True)
    walmart_inStore = models.BooleanField(default=False)    
    price = models.CharField(
        max_length=128, blank=True, null=True)
    url = models.CharField(
        max_length=256, blank=True, null=True)
    inStore_stockStatus = models.CharField(
        max_length=128, blank=True, null=True)
    

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        
    def __unicode__(self):
        return self.name
        
        
class Configuration(models.Model):
    i_config = models.AutoField(primary_key=True, verbose_name='Sr. No#')
    storeId = models.CharField(
        max_length=128, default='1768')

    class Meta:
        db_table = 'settings'
        verbose_name = 'Configuration'
        verbose_name_plural = 'Configurations'
        
    def __unicode__(self):
        return self.storeId
