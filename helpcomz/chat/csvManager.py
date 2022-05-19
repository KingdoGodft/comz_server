import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import csv
import json
import numpy
import pandas
import re
import codecs
from collections import namedtuple
import logging
logger = logging.getLogger("sex")

class KeywordCsvData:
    def __init__(self, keyword, rank):
        self.keyword = keyword
        self.rank = rank


def isValidJson(myStr):
    myStr = re.sub('[^\'\":{},]', '', myStr)
    stack = []
    if len(myStr) == 0:
        return False
    if myStr.count(':') < 1:
        return False
    if myStr.count('"') < 4 and myStr.count("'") < 4:
        return False
    if myStr.count('{') != myStr.count('}'):
        return False
    if myStr.count('{') < 1 or myStr.count('}') < 1:
        return False
    
    for i in range(0,len(myStr)):
        try:
            char = myStr[i]
            
            if char == '{':
                stack.append(char)
            elif char == '"':
                stack.append(char)
            elif char == "'":
                stack.append(char)
            elif char == ',':
                
                charCount = 0
                
                while True:
                    popChar = stack.pop()
                    
                    
                    if popChar == ':':
                        break
                    
                    charCount += 1
                    
                    if popChar != '"' and popChar != "'":
                        return False
                    
                    if len(stack)==0:
                        return False
                    
                if charCount != 2 and charCount != 0:
                    return False
                
                
                popChar1 = stack.pop()
                popChar2 = stack.pop()
                
                if popChar1 == popChar2 == '"' or popChar1 == popChar2 == "'":
                    pass
                else:
                    return False
            elif char == ':':
                stack.append(char)
            elif char == '}':
                charCount = 0
                
                while True:
                    popChar = stack.pop()
                    
                    
                    if popChar == ':':
                        break
                    
                    charCount += 1
                    
                    if popChar != '"' and popChar != "'":
                        return False
                    
                    if len(stack)==0:
                        return False
                    
                if charCount != 2 and charCount != 0:
                    return False
                
                
                popChar1 = stack.pop()
                popChar2 = stack.pop()
                
                if ((popChar1 == popChar2) and (popChar2 == '"' or popChar2 == "'")):
                    pass
                else:
                    return False
                
                if stack.pop() != '{':
                    return False
            else:
                return False

            
        except:
            return False
    if len(stack) == 0:
        return True
    return False
            
        
class Generic:
    @classmethod
    def from_dict(cls, dict):
        obj = cls()
        obj.__dict__.update(dict)
        return obj

class TestClass():
    def __init__(self, field1, field2, field3, keyword, rank):
        self.field1 = field1
        self.field2 = field2
        self.field3 = TestClass2(999,888,'text1','text2')
        self.keyword = keyword
        self.rank = rank
        
class TestClass2():
    def __init__(self,a,b,c,d):
        self.a = a
        self.b = b
        self.c = TestClass3('text3','text4',321431211,2498918)
        self.d = d
        
class TestClass3():
    def __init__(self,e,f,g,h):
        self.e = e
        self.f = f
        self.g = g
        self.h = h
        

class CsvManager:
    def __init__(self, file):
        self.file = file
        logger.debug(os.getcwd())

        self.data = pandas.read_csv(file,error_bad_lines=False)
        # print(self.data)
        # print(self.data)
        self.header = self.data.columns
        
    def reset(self, file):
        self.file = file
        self.data = pandas.read_csv(file)
        self.header = self.data.columns
    def resetNoFile(self):
        self.reset(self.file)
    
    def save(self):
        self.data.to_csv(self.file,index=False)
        
    def consumeRow(self, colName=None, key=None, consume=True, consumeAll=False):
        if consumeAll == True:
            returnData = self.data
        else:
            returnData = self.data[self.data[colName] == key]
        returnList = []
        
        for row in returnData.iloc:
            returnObject = {}
            for col in returnData.columns:
                # print(col)
                strData = str(row[col])

                # if isValidJson(strData):
                #     replacedString = str(strData.replace("'","\""))
                #     returnObject[col] = json.loads(replacedString, object_hook=Generic.from_dict)
                # else:
                #     returnObject[col] = row[col]
                try:
                    replacedString = str(strData.replace("'","\""))
                    # print(replacedString)
                    returnObject[col] = json.loads(replacedString, object_hook=Generic.from_dict)
                except:
                    returnObject[col] = row[col]
            returnList.append(returnObject)
        
        if consume == True:
            if consumeAll == False:
                self.data = self.data[self.data[colName] == key]
            else:
                self.data = self.data.iloc[0:0]
                
            # self.save()
       
        return returnList
    
    def consumeFirstRow(self):
        if self.data.shape[0] == 0:
            return
        
        returnData = self.data.iloc[0:1]

        returnList = []
        
        for row in returnData.iloc:
            returnObject = {}
            for col in returnData.columns:
                strData = str(row[col])

                if isValidJson(strData):
                    replacedString = str(strData.replace("'","\""))
                    returnObject[col] = json.loads(replacedString, object_hook=Generic.from_dict)
                else:
                    returnObject[col] = row[col]
            returnList.append(returnObject)
        
        
        self.data = self.data.iloc[1:]
        self.save()
        
        return returnList[0]
    
    def checkEmpty(self):
        return self.data.shape[0] == 0
        
        
    def addRow(self, obj, isDict=False):
        if isDict==False:
            mydict = self.convertObjToJson(obj)
        else:
            mydict = obj
        df = pandas.DataFrame([mydict])

        self.data = self.data.append(df)
        self.save()
    
    def addRows(self, objList, isDict=False):
        for obj in objList:
            if isDict==False:
                mydict = self.convertObjToJson(obj)
            else:
                mydict = obj
            df = pandas.DataFrame([mydict])
            self.data = self.data.append(df)
            
        self.save()
        
        
    @staticmethod
    def convertObjToJson(obj):
        result = {}
        for key in obj.__dict__:
            if hasattr(getattr(obj,key), '__dict__'):
                
                flag = True
                temp = getattr(obj,key)
                
                for underKey in temp.__dict__:
                    if hasattr(getattr(temp,underKey),'__dict__'):
                        flag = False
                        break
                if flag == False:    
                    result.update( [(key, CsvManager.convertObjToJson(getattr(obj,key)))] )
                else:
                    result.update( [(key, temp.__dict__)] )
                    
            else:
                result.update([(  key, getattr(obj,key)  )])
        
        
        return result