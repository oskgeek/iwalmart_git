import os
import datetime
import xlsxwriter

from django.db.models import Q
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.admin import SimpleListFilter
from django.contrib.contenttypes.models import ContentType


from InStoreStockAnalyzer.models import Department, Products, Configuration
from InStoreStockAnalyzer.utils import InStoreStockAnalyzer


class DepartmentListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = ('name')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'parentId'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        query = ~Q(name__contains=':-')
        lookup_tuple = Department.objects.filter(query).values_list('parentId', 'name')
        return tuple(lookup_tuple)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        return queryset.filter(parentId=self.value())

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('i_department', 'name',)
    ordering = ('name',)
    list_filter = (DepartmentListFilter,)
    actions = ('populate_products', 'view_products', 'export_products_to_excel',)

    def get_queryset(self, request):
        qs = super(DepartmentAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            query = ~Q(browseToken=None)
            return qs.filter(query)
        return qs
    
    def has_add_permission(self, request):
        return False
        
       
    def populate_products(self, request, queryset):
        walmart = InStoreStockAnalyzer()
        walmart.StoreId = Configuration.objects.all()[0].storeId
        selc_objects = queryset.all()
        for obj in selc_objects:
            if obj.browseToken is not None:
                p_products = walmart.getProducts(obj.browseToken)
                p_objects = list()
                for items in p_products:
                    print "----------------------Items"
                    walmart.getStockUrls(items)
                    for item in items:                    
                        args = {
                            'i_department' : obj,
                            'iD' : item['iD'],
                            'upc' : None,
                            'name' : item['name'],
                            'walmart_availability' : item['itemAvailability']['availability'],
                            'walmart_inStore' : item['itemAvailability']['inStore'],
                            'price' : item['price'],
                            'url' : item['url'],
                            'inStore_stockStatus' : None,
                        }
                        p_objects.append(Products(**args))
                walmart.getInStoreInfo(p_objects)
                Products.objects.bulk_create(p_objects)
        messages.success(request, "Successfully created products for selected category.")
    populate_products.short_description = "Generate Products"
   
    def view_products(self, request, queryset):
        redirect_url = "/admin/InStoreStockAnalyzer/products/?i_department__i_department=%s"
        if queryset.count() > 0:
            selected = queryset.all()[0].i_department
            redirect_url = redirect_url % selected
        return HttpResponseRedirect(redirect_url)

    def export_products_to_excel(self, request, queryset):
        file_name = 'Walmart_InStoreStock_%s.xlsx' % datetime.datetime.now()
        path_dir = os.path.join(settings.MEDIA_ROOT + "files_library/")
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
        FilePath = os.path.join(path_dir, file_name)
        workbook = xlsxwriter.Workbook(FilePath)
        worksheet = workbook.add_worksheet("Products")
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:G', 20)
        worksheet.set_column('H:H', 70)
        worksheet.set_column('I:XFD', None, None, {'hidden': True})
        style = workbook.add_format({'bold':1, 'font_size': 9})
        dstyle = workbook.add_format({'font_size': 9})    
                           
        if queryset.count() > 0:
            for selcDept in queryset.all():                
                pset = selcDept.products_set.all()
                idx = 1 
                worksheet.write('A1', 'Department Name', style)
                worksheet.write('B1', 'Product Name', style)
                worksheet.write('C1', 'UPC', style)
                worksheet.write('D1', 'Price', style)
                worksheet.write('E1', 'Local Store Stock', style)
                worksheet.write('F1', 'Walmart Availability', style)
                worksheet.write('G1', 'Walmart Stock', style)
                worksheet.write('H1', 'Url', style)
                for op in pset:
                    loc = 'A%s' % str(idx)
                    worksheet.write(loc, op.i_department.name, dstyle)
                    worksheet.write(loc.replace('A','B'), op.name, dstyle)
                    worksheet.write(loc.replace('A','C'), op.upc, dstyle)
                    worksheet.write(loc.replace('A','D'), op.price, dstyle)
                    worksheet.write(loc.replace('A','E'), op.inStore_stockStatus, dstyle)
                    worksheet.write(loc.replace('A','F'), op.walmart_availability, dstyle)
                    worksheet.write(loc.replace('A','G'), str(op.walmart_inStore), dstyle)
                    worksheet.write_url(loc.replace('A','H'), op.url, dstyle)
                    idx+=1   
                    
        download_path = FilePath.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
        return HttpResponseRedirect(download_path)
                
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('i_product', 'iD', 'name', 'upc', 'walmart_availability', 'inStore_stockStatus', 
                        'walmart_inStore', 'price', 'url',)
    ordering = ('name',)
    list_filter = ('i_department__name',)
    actions = ('export_all_products_to_excel',)

    def get_queryset(self, request):
        qs = super(ProductsAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs
    
    def has_add_permission(self, request):
        return False
        
    def export_all_products_to_excel(self, request, queryset):
        file_name = 'Walmart_InStoreStock_%s.xlsx' % datetime.datetime.now()        
        path_dir = os.path.join(settings.MEDIA_ROOT + "files_library/")
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
        FilePath = os.path.join(path_dir, file_name)
        workbook = xlsxwriter.Workbook(FilePath)
        worksheet = workbook.add_worksheet("Products")
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:G', 20)
        worksheet.set_column('H:H', 70)
        worksheet.set_column('I:XFD', None, None, {'hidden': True})
        style = workbook.add_format({'bold':1, 'font_size': 9})
        dstyle = workbook.add_format({'font_size': 9})    
        idx = 1         
        for product in Products.objects.all():                            
            worksheet.write('A1', 'Department Name', style)
            worksheet.write('B1', 'Product Name', style)
            worksheet.write('C1', 'UPC', style)
            worksheet.write('D1', 'Price', style)
            worksheet.write('E1', 'Local Store Stock', style)
            worksheet.write('F1', 'Walmart Availability', style)
            worksheet.write('G1', 'Walmart Stock', style)
            worksheet.write('H1', 'Url', style)
            loc = 'A%s' % str(idx)
            worksheet.write(loc, product.i_department.name, dstyle)
            worksheet.write(loc.replace('A','B'), product.name, dstyle)
            worksheet.write(loc.replace('A','C'), product.upc, dstyle)
            worksheet.write(loc.replace('A','D'), product.price, dstyle)
            worksheet.write(loc.replace('A','E'), product.inStore_stockStatus, dstyle)
            worksheet.write(loc.replace('A','F'), product.walmart_availability, dstyle)
            worksheet.write(loc.replace('A','G'), str(product.walmart_inStore), dstyle)
            worksheet.write_url(loc.replace('A','H'), product.url, dstyle)
            idx+=1   
                    
        download_path = FilePath.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
        return HttpResponseRedirect(download_path)
     
        
        
class ConfigurationAdmin(admin.ModelAdmin):
            
    def has_add_permission(self, request):
        return False
    
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.disable_action('delete_selected') 
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Products, ProductsAdmin)
admin.site.register(Department, DepartmentAdmin)


