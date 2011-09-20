#!/usr/bin/python -tt

import sys
import re
import copy

#Global map of Suitability Score (SS) and customer, product pair 
cust_prod_ss = {}

#Global common factors
common_facts = {}

#master list of combinations
master_list = {}

#minumum rejected SS
min_rej = {}

def map_reduce(i,mapper,reducer):
  intermediate = [] 

  #For each input line get a list of tuples of cust, prod, SS combination 
  for (key,value) in i.items():
    intermediate.extend(mapper(key,value))

  #For each tuple list get max SS
  for i in intermediate:
    if i[1]:
      ss_list = [get_max_ss(i[0], i[1], 0, prod, i[2]) for prod in i[2]]
      #Find max ss from ss_list
      print '%.2f'%reduce(max, ss_list)

#For given product find max SS in the cust_prod_list
#Find available list of cust, prod, SS tuples given selected cust prod
#Find rejected list of cust, prod, SS tuples given selected cust prod
#Calculate rejected SS
#If rejected SS is more than min_rej then abort the execution else continue
#If rejected SS is less than min_rej then reset min_rej
#Delete prod from the list of prods
#For remaining prods call get_max_ss with available list of tuples and 
#new rejected SS
#max_ss = selected SS + max ss of remaining prod list
def get_max_ss(line_key, cust_prod_list, rej, prod, prods):
  global master_list, min_rej

  #If rejected ss is more than min_rej then abort further execution
  if min_rej[line_key] != float('inf') and rej >= min_rej[line_key]:
    return 0

  #Find max SS for given prod
  prod_ss_list = filter(lambda x: get_cust_prod(prod, x), cust_prod_list)
  prod_ss_list = sorted(prod_ss_list, key=sort_by_ss, reverse = True)
  
  selected_item = prod_ss_list[0]
  ss = selected_item[2]
  cust_name = selected_item[0]
  prod_name = selected_item[1]

  #Find available list of cust, prod, SS given selected cust_name, prod_name
  new_list = filter(lambda x: available_cust_prod(cust_name, prod_name, x), cust_prod_list) 

  #Find rejected list of cust, prod, SS tuples given selected cust prod
  rej_list = filter(lambda x: rej_cust_prod(cust_name, prod_name, x), cust_prod_list) 

  rej_ss = rej
  if rej_list:
    rej_ss_t = reduce(add_ss, rej_list)
    #subtract selected SS from rej_ss
    rej_ss += rej_ss_t[2] - ss
  if not new_list:
    if min_rej[line_key] == float('inf'):
      min_rej[line_key] = rej_ss
    else:
      if min_rej[line_key] > rej_ss:
        min_rej[line_key] = rej_ss
    return ss

  #Key representing curren combination of cust, prod, ss tuples
  master_key = str(new_list)
  max_ss = 0
  try:
    #Check if the max_ss for given combination is already calculated
    max_ss = master_list[master_key] 
  except KeyError:
    new_prods = prods[:]
    new_prods.remove(prod)
   
    ss_list = [get_max_ss(line_key, new_list, rej_ss, prod, new_prods) for prod in new_prods]
    if ss_list:
      max_ss = reduce(max, ss_list)
    #Store max_ss for a given key
    master_list[master_key] = max_ss 

  #max ss = selected ss + max ss for remaining prods
  max_ss += ss 

  return max_ss 

#Get available list of customers and products given selected cust and prod 
def available_cust_prod(cust, prod, item):
  return item[0] != cust and item[1] != prod

#Get rejected list of customers and products given selected cust and prod
def rej_cust_prod(cust, prod, item):
  return item[0] == cust or item[1] == prod

#Get list of customers and products for a selected prod
def get_cust_prod(prod, item):
  return item[1] == prod

#Sort cust, prod, ss combination by ss
def sort_by_ss(item):
  return item[2]

#Find max among i and j
def max(i, j):
  if i > j:
    return i
  else:
    return j

#Add SS of given cust, prod, ss tuples
def add_ss(i, j):
  return (1,2,i[2]+ j[2])

#For each input line get cust and prod details, 
#calculate SS for each cust-prod combination
def mapper(input_key,input_value):
  global min_rej

  #get cust, prod details
  custs, prods, prod_names = populateCustsProds(input_value.strip().lower())

  #get combinations fo cust, prod and ss
  cust_prod_list = [calculateSS(cust, prod) for cust in custs for prod in prods]

  #default rejected SS for each input line is set to infinite 
  min_rej[input_key] = float('inf')

  return [(input_key, cust_prod_list, prod_names)]

#Read an input file and calculate SS
def getAllSS(filename):

  file = open(filename, 'r')

  i = {}
  counter = 0

  #populate a map with each line in the file
  for line in file.readlines():
    i[counter] = line
    counter = counter + 1

  file.close()

  #Execute mapper, reducer on each entry in the map
  map_reduce(i,mapper,reducer=None)

#Find if two elements have a common factor other than 1
def hasCommonFactor(a, b):
  if b < 2:
    return False
  r = a % b
  if r == 1:
    return False
  if r == 0:
    return True

  a = b
  b = r
  return hasCommonFactor(a, b)

#Find num_vow, num_con, num_let for a cust name
def getCustDetails(name):
  letters = re.findall(r'[a-z]', name)
  num_let = len(letters)
  #get number of vowels
  num_vow = len(re.findall(r'[aeiouy]',name))
  #get number of consonants
  num_con = num_let - num_vow
  #create a customer object
  cust = {"name": name, "num_vow": num_vow, "num_con": num_con, "num_let": num_let}
  return cust

#Find num_let, is_odd for a product name 
def getProdDetails(name):
  letters = re.findall(r'[a-z]', name)
  #get number of letters
  num_let = len(letters)
  is_odd = num_let % 2
  #create a product object
  prod = {"name": name, "is_odd": is_odd, "num_let": num_let}
  return prod

#Populate a list of customers and a list of products based on
#an input line
#Customer attributes: name, num of vowels, num of consonants, num of letters
#Product attributes: name, num of letters, num of letters
def populateCustsProds(line):

  #Separate customer and product info
  line_parts = line.split(';')

  cust_info = ""
  prod_info = ""

  custs = []
  prods = []
  cust_names = []
  prod_names = []
  #If both customer and product info is available then
  #extract further information about customers and products
  #and populate custs and prods lists
  #If customer or product info is missing then return empty
  #custs and prods lists
  if len(line_parts) == 2:
    cust_info = line_parts[0]
    prod_info = line_parts[1]

    #if cust_info or prod_info is empry then return empty
    #customer and product lists
    
    if not cust_info or not prod_info:
      return custs, prods, prod_names
    #get a list of customer names
    cust_names = cust_info.split(',')
    #get a list of product names
    prod_names = prod_info.split(',')

    custs = map(getCustDetails, cust_names)
    #for each customer find num of vowels, num of consonants, num of letters
    #and generate a list of customers

    prods = map(getProdDetails, prod_names)
    #for each product find num of letters, and if it has odd or even num of letters
    #and generate a list of products

  return custs, prods, prod_names

#Calculate SS for a set of customers and products
#Rules: 
#1. If the number of letters in the product's name is even then the SS is the number 
#of vowels (a, e, i, o, u, y) in the customer's name multiplied by 1.5.
#2. If the number of letters in the product's name is odd then the SS is the number 
#of consonants in the customer's name.
#3. If the number of letters in the product's name shares any common factors (besides 1) 
#with the number of letters in the customer's name then the SS is multiplied by 1.5.

def calculateSS(cust, prod, cust_prod=""):

  cust_prod = cust["name"]+prod["name"]
  ss = 0
  global cust_prod_ss, common_facts
  #check if the given customer product pair has been considered earlier
  #if yes then get the pre-calculated SS
  #if not then calculate the SS
  try:
    return (cust["name"], prod["name"], cust_prod_ss[cust_prod])
  except:
    pass

  #check if num of letters in product are even or odd
  if prod["is_odd"]:
    #if product num_let is odd then ss = num of consonants
    ss = cust["num_con"]
  else:
    #if product num_let is even then ss = num of vowels * 1.5
    ss = cust["num_vow"] * 1.5

  #default multiplier
  multiplier = 1

  #check if num of letters in product name and num of letters in
  #customer name has a common factor
  min = cust["num_let"]
  max = prod["num_let"]
  if min > max:
    max = cust["num_let"]
    min = prod["num_let"]

  try:
    if common_facts[str(min)+"-"+str(max)]:
      multiplier = 1.5
  except KeyError:
    common_facts[str(min)+"-"+str(max)] = hasCommonFactor(cust["num_let"], prod["num_let"])
    if common_facts[str(min)+"-"+str(max)]:
      multiplier = 1.5

  ss = ss * multiplier
  #add SS in a map of SS for customer-product pair
  cust_prod_ss[cust_prod] = ss
  return (cust["name"], prod["name"], ss)  

def main():
  #check if filename argument is provided on the commandline
  if len(sys.argv) < 2:
    print "\nUsage: discount_offers./py <filename>"
    sys.exit()

  #get filename
  filename = sys.argv[1]

  #get cumulative SS for all input lines in the file
  getAllSS(filename)
  sys.exit(0)


if __name__ == "__main__":
  main()
