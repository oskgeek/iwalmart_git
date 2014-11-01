#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  InStoreStockAnalyzer.py
#  
#  Copyright 2014 OsamaRasheed <osamarasheed@osygeek>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
import os
import requests 
import grequests 
import datetime 
import xlsxwriter
from threading import Thread


class InStoreStockAnalyzer:
    Taxonomy  = 'http://api.mobile.walmart.com/taxonomy/departments/?depth=3'
    Category  = 'http://api.mobile.walmart.com/taxonomy/departments/%s'
    Products  = 'http://mobile.walmart.com/m/j?service=Browse&method=browseByToken&'
    Products += 'p1={0}%3D&p2=All&p3=RELEVANCE&p4={1}&p5={2}&e=1&40cc=1'
    InStore   = 'https://mobile.walmart.com/m/j?service=Slap&method=getByItemsAndStores&'
    InStore   += 'p1=[{0}]&p2=[{1}]&p3=c4tch4spyder&version=3&e=1'
    StoreId  =  '1768'
    Departments = list()
    DepartmentCategories = list()
    ProductsList = list()
    StockUrls = list()
    
    def __init__(self):
        pass
        
    def getDepartments(self, child, pName=None):    
        try:
            if isinstance(child, dict):
                parent_name = child['name']
                parent_category = child['category']
                if pName is not None:
                    parent_name = '%s:- %s' % (pName, child['name'])
                if bool(child['parentCategories']) is True:
                    parent_category = child['parentCategories'][0]
                args = {'category': child['category'], 'iD' : child['id'],
                        'name' : parent_name, 'parentId': parent_category,
                }
                if child.has_key('browseToken'):
                    args.update({'browseToken': child['browseToken']})
                self.Departments.append(args)
                if child.has_key('children'):
                    self.getDepartments(child['children'], parent_name)
            elif isinstance(child, list):        
                for child in child:
                    self.getDepartments(child, pName)
        except Exception as ex:
            print ex

    def getProductslen(self, browseToken):
        url = self.Products.format(browseToken, 0, 20)
        r = requests.get(url)
        response = r.json()
        return int(response['totalCount'])

    def getUrls(self, browseToken):
        url_list = list()
        pRange = self.getProductslen(browseToken) / 100
        startIndex, lastIndex = 0, 100
        for p in range(0, pRange+1): 
            url_list.append(self.Products.format(browseToken, startIndex, lastIndex))
            startIndex += lastIndex
        return url_list
                
    def getProducts(self, browseToken):
        products = list()
        try:                 
            urls = self.getUrls(browseToken)
            rs = (grequests.get(u) for u in urls)
            response = grequests.map(rs, size=10)   
            for req in response:
                if req.status_code == requests.codes.ok:
                    result = req.json()
                    if result.has_key('item'):
                        products.append(result['item'])
        except Exception as ex:
            print ex
        return products
    
    def getStockUrls(self, products):
        try:
            for p in products:
                self.StockUrls.append(self.InStore.format(p['iD'], self.StoreId))        
        except Exception as ex:
            print ex            
          
    def getInStoreInfo(self, p_objects):   
        upc, stockStatus = '', 'Not Available'
        try:
            rs = (grequests.get(u) for u in self.StockUrls)
            response = grequests.map(rs, size=10)  
            for req, pb in zip(response, p_objects):
                print "----------------------Stocks"
                if req.status_code == requests.codes.ok:
                    result = req.json()
                    if bool(result) == True:
                        pb.inStore_stockStatus = result[0]['stores'][0]['stockStatus']
                        pb.upc = result[0]['item']['upc']
        except Exception as ex:
            print ex
        return p_objects
        
    def writeWalmartRawDataToExcel(self):
        try:
            print "Writng Excel Sheet Now! %s" % datetime.datetime.now()
            wDirectory = os.path.dirname(os.path.abspath(__file__)) 
            FilePath = os.path.join(wDirectory, 'InStoreStockComparison.xlsx')
            workbook = xlsxwriter.Workbook(FilePath)
            worksheet = workbook.add_worksheet("Walmart_Stock_Comparison")
            worksheet.set_column('A:A', 70)
            worksheet.set_column('B:E', 30)
            worksheet.set_column('F:XFD', None, None, {'hidden': True})
            style = workbook.add_format({'bold':1, 'font_size': 9})
            idx = 1
            for item in self.ProductsList:
                loc = 'A%s' % str(idx)
                worksheet.write(loc, item['category'], style)
                worksheet.write(loc.replace('A','B'), 'Price', style)
                worksheet.write(loc.replace('A','C'), 'Walmart InStore Status', style)
                worksheet.write(loc.replace('A','D'), 'Walmart Stock Status', style)
                worksheet.write(loc.replace('A','E'), 'Url', style)
                idx+=1                
                for sitems in item['products']:
                    dstyle = workbook.add_format({'font_size': 9})
                    loc = 'A%s' % str(idx)
                    purl = 'http://mobile.walmart.com/ip/%s' % str(sitems['iD'])
                    worksheet.write(loc, sitems['name'], dstyle)
                    worksheet.write(loc.replace('A','B'), sitems['price'], dstyle)
                    worksheet.write(loc.replace('A','C'), sitems['inStore'], dstyle)
                    worksheet.write(loc.replace('A','D'), sitems['availability'], dstyle)
                    worksheet.write_url(loc.replace('A','E'), purl, style)
                    idx+=1
            workbook.close()
            print "Writng Excel Sheet Completed! %s" % datetime.datetime.now()
        except Exception as ex:
            print 'Failed while writing walmart data to excel sheet. Error: ', repr(ex)


def main():
    try:
        pass
    except Exception as ex:
        print "Error: unable to start thread", repr(ex)
    
    return 0

if __name__ == '__main__':
    main()

