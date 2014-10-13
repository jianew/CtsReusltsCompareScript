#!/usr/bin/env python
#-*- coding:utf-8 -*-

from xml.etree import ElementTree as ET 
import sys
from collections import defaultdict
import os
from pyExcelerator import *

class CtsResultParser:

   def __init__(self, xmlname):
      self.xmlname = xmlname
      self.testresult={}

   def parse(self):
      tree = ET.parse(self.xmlname)
      root = tree.getroot()
      #except Exception, e:
       #  print "Error: cannot parse file :%s"%(self.xmlname)         
      testpacs = root.findall("TestPackage")
      for pnode in testpacs:
         self.parse_TestPackage(pnode)

   def parse_TestPackage(self, pnode):
      testpackagename = pnode.get("name")
      apppackagename = pnode.get("appPackageName")
      apppackagename += "/"
      for snode in pnode:
         self.parse_TestSuite(snode, apppackagename)
      
   def parse_TestSuite(self, snode , psname):
      sname = snode.get("name")
      for node in snode:
         if node.tag == "TestSuite":
            self.parse_TestSuite(node, psname + "." + sname)
         elif node.tag == "TestCase":
            self.parse_TestCase(node, psname + "." + sname)


   def parse_TestCase(self, cnode, suitepath):
      cname = cnode.get("name")
      for tnode in cnode:
         assert(tnode.tag == "Test")
         self.parse_Test(tnode , suitepath + "." + cname)

   def parse_Test(self, tnode, suitpath):   
      testname = suitpath + "." +tnode.get("name")
      result = tnode.get("result")
      self.testresult[testname] = result

   def get_result(self, path):
      if self.testresult.has_key(path):
         return self.testresult[path]
      else:
         return None
   
   def get_failed_results(self):
      res = []
      for name, result in self.testresult.iteritems():
         if result == "fail":
            res.append(name)
      return res

   def get_pass_results(self):
      res = []
      for name, result in self.testresult.iteritems():
         if result == "pass":
            res.append(name)
      return res

   def get_notExecuted_results(self):
      res = []
      for name, result in self.testresult.iteritems():
         if result == "notExecuted":
            res.append(name)
      return res
            

   def get_lists_failed_results(self,inlists):
      res = []
      for i in inlists:
         if self.get_result(i) == "fail":
            res.append(i)
         elif self.get_result(i) == None:
            res.append(i)
      return res


   def get_lists_pass_results(self,inlists):
      res = []
      for i in inlists:
         if self.get_result(i) == "pass":
            res.append(i)
      return res
   
   def print_stats(self):
      print "STASTICS:\r"
      print "total test cases:%d\r"%(len(self.testresult))
      print "failed cases:%d\r"%(len(self.get_failed_results()))
      print "pass cases:%d\r"%(len(self.get_pass_results()))
      print "notExecuted cases:%d\r"%(len(self.get_notExecuted_results()))

   def eat(self, ano):
      for name,res in ano.testresult.iteritems():
         if self.testresult.has_key(name):
            if res == "pass" or self.testresult[name] == "pass":
               self.testresult[name]="pass"
            elif res == "fail" or self.testresult[name] == "fail":
               self.testresult[name]="fail"
            else:
               self.testresult[name]="notExecuted"
         else:
            self.testresult[name] = res
      return self
            
def formatname(inname):
   packagename,testname = inname.split("/")
   testnamesplits = testname.split(".")
   classname = ".".join(testnamesplits[1:-1])
   testname = testnamesplits[-1]
   return packagename, classname, testname

def output(names):
   package=defaultdict(lambda : defaultdict(list))
   for name in names:
      p,c,t = formatname(name)
      package[p][c].append(t)

   for x,y in package.iteritems():
      print "PACKAGENAME:  %s:\r"%(x)
      for z,a in y.iteritems():
         print "            CLASSNAME: %s:\r"%(z)
         for i in a:
            print "                           %s\r"%(i)

def xls_produce(names):
   w = Workbook()
   ws = w.add_sheet("ctscompare")

   package=defaultdict(lambda : defaultdict(list))
   for name in names:
      p,c,t = formatname(name)
      package[p][c].append(t)

   line = 0
   
   for x,y in package.iteritems():
      ws.write(line,0,str(x))
      for z,a in y.iteritems():
         ws.write(line,1, str(z))
         for i in a:
            ws.write(line,2,str(i))
            line+=1
   w.save('compare.xls')


def get_all_xmls(dir32, dir64):
   xmldir32s = os.listdir(dir32)
   xmldir64s = os.listdir(dir64)
   xmldir32s = map(lambda x:dir32+"/"+x+"/testResult.xml", xmldir32s)
   xmldir64s = map(lambda x:dir64+"/"+x+"/testResult.xml", xmldir64s)
   return xmldir32s,xmldir64s

if __name__ == "__main__":

 #  if sys.argv.count("-32") == 0 or sys.argv.count("-64") == 0:
  #    print "the input order is :  -32 32bitresult.xml.... -64  64bitresult.xml..."
   #   exit
   
 #  results32xml = sys.argv[sys.argv.index("-32")+1:sys.argv.index("-64")]
 #  results64xml = sys.argv[sys.argv.index("-64")+1:]
   if len(sys.argv) != 3:
      print "the intput order is : dir_for_32_original_results dir_for_64_original_results"
      exit
   results32xml,results64xml = get_all_xmls(sys.argv[1], sys.argv[2])

   p1 = CtsResultParser(results32xml[0])
   p1.parse()
   for i in results32xml[1:]:
      temp = CtsResultParser(i)
      temp.parse()
      p1.eat(temp)
   print "32bit"
   p1.print_stats()
   p2 = CtsResultParser(results64xml[0])
   p2.parse()   
   for i in results64xml[1:]:
      temp = CtsResultParser(i)
      temp.parse()
      p2.eat(temp)
   print "64bit"
   p2.print_stats()
   p2fails = p2.get_failed_results()
   #print p2fails
   p2fails_p1pass = p1.get_lists_pass_results(p2fails)
   print "\n"*3
   print "64 fails but 32 pass :"
   print "nums: %d"%(len(p2fails_p1pass))
   output(p2fails_p1pass)
   xls_produce(p2fails_p1pass)
