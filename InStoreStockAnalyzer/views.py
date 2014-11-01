import requests

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages

from InStoreStockAnalyzer.models import Department
from InStoreStockAnalyzer.utils import InStoreStockAnalyzer

def populate_departments(request):
    try:    
        url = 'http://api.mobile.walmart.com/taxonomy/departments/?depth=3'
        r = requests.get(url)
        result = r.json()
        walmart = InStoreStockAnalyzer()
        walmart.getDepartments(result['children'])
        deptObjects = list()    
        for child in walmart.Departments:
            obj = Department(**child)
            deptObjects.append(obj)
        Department.objects.bulk_create(deptObjects)
    except Exception as ex:
        return HttpResponse (repr(ex))        
    context = {'message' : 'Successfully created',}
    return render(request, 'InStoreStockAnalyzer/index.html', context)

