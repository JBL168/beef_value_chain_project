import pandas as pd
import pymupdf as fitz
import re
import os

os.chdir(r'C:\Users\baoxi\Documents\TAMU\Fall_2024\RESEARCH_ML\Working\2019_2023')

def get_df_from_file(file):
    # opening the pdf
    doc = fitz.open(file)

    # extract base file name without extension for image
    # file_name = os.path.splitext(os.path.basename(pdf_file))[0]
    # print(file_name)

    # initialize lists for columns of interest
    items_names = []
    values = []

    # obtaining the year
    yearVal = int(file[0:4])

    # define major categories and subcategories
    major_categories = {
        "Year": ["Year", yearVal],
        "Number of Head": [],
        "Buy Weight": [],
        "Buy Price": [],
        "Sell Weight": [],
        "Sell Price": [],

        # other info
        "Total Revenue": [],
        "Total Variable Costs": [],
        "Total Fixed Costs": [],
        "Profit": [],

        # revenue
        "Stocker": [], # this has an issue where there is an invisible "Stocker" string in the pdf

        #variable costs
        "Stocker Purchase": [],
        "Stocker Delivery": [],
        "Grazing": [],
        "Health": [],
        "Feed": [],
        "Miscellaneous": [],
        "Fuel": [],
        "Lube (As a % of fuel)": [],
        "Utilities": [],
        "Repairs": [],
        "Marketing": [],
        "Labor": [],
        "Interest on Credit Line": [],

        # fixed costs
        "Depreciation": [],
        "Equipment Investment": [], # incorrect
        "Management Fee, Owner/Operator Labor": []
        
    }

    data = []

    # loop through each pdf page
    for page in doc:
        
        # store page in png
        # pix = page.get_pixmap(dpi = 200)
        # pix.save(f"{file_name}-page-{page.number+1}.png")

        text = page.get_text()
        # print(text)

        lines = text.split("\n")
        # print(lines)

        i = 0

        # looping through each item
        while (i < len(lines)): 
            lines[i] = lines[i].strip()

            # checks if the category is a major category
            if lines[i] in major_categories.keys():
                # hard coded checking for the category stocker for profitability. 
                if (lines[i] == "Stocker" and any(char.isalpha() for char in lines[i+1])):
                    i += 1
                    continue
                elif (lines[i] == "Stocker"): # for stocker category
                    templist = []
                    templist.append(lines[i])
                    for j in range(1,7):
                        if (not any(char.isalpha() for char in lines[i+j])):
                            val = float(re.sub('[%$,]', '', (lines[i+j])))
                            templist.append(val)
                        else: 
                            templist.append(lines[i+j])
                    major_categories[lines[i]].append(templist)
                    i += 7
                    continue
                elif (lines[i] == "Interest on Credit Line"):
                    val = float(re.sub('[%$,]', '', (lines[i+2])))
                    major_categories[lines[i]] = [lines[i], val]
                    i += 4
                    continue
                elif (lines[i] == "Total Revenue" or lines[i] == "Total Variable Costs" or lines[i] == 'Total Fixed Costs'):
                    val = float(re.sub('[%$,]', '', (lines[i+1])))
                    major_categories[lines[i]] = [lines[i], val]
                    i += 3
                    continue
                elif (lines[i] == "Equipment Investment"):
                    val = float(re.sub('[%$,]', '', (lines[i+4])))
                    major_categories[lines[i]] = [lines[i], val]
                    i += 3
                    continue
                elif (lines[i] == 'Number of Head'):
                    val = float(re.sub('[%$,]', '', (lines[i+1])))
                    major_categories[lines[i]] = [lines[i], val]
                    i += 2
                elif (not any(char.isalpha() for char in lines[i+1])): #check if the category does not contain subcategories
                    if (any(char == '$' for char in lines[i+1])):
                        val = float(re.sub('[%$,]', '', (lines[i+1])))
                        major_categories[lines[i]] = [lines[i], val]
                        i += 2
                        # loop until next major category
                        while not(lines[i] in major_categories.keys()):
                            i += 1
                        continue
                    else:
                        templist = []
                        templist.append(lines[i])
                        for j in range(1,6):
                            if (not any(char.isalpha() for char in lines[i+j])): # appends value after converting to number & removing symbols
                                val = float(re.sub('[%$,]', '', (lines[i+j])))
                                templist.append(val)
                            else: # appends non-numerical values to the list
                                templist.append(lines[i+j])
                        major_categories[lines[i]].append(templist)
                        i += 6
                        continue
                else: #else (major category contains subcategories)
                    currMajor = lines[i]
                    i += 1 # enter the subcategory
                    while True: #loops until next major category
                        templist = []
                        templist.append(lines[i])
                        for j in range(1,6):
                            if (not any(char.isalpha() for char in lines[i+j])):
                                val = float(re.sub('[%$,]', '', (lines[i+j])))
                                templist.append(val)
                            else: 
                                templist.append(lines[i+j])
                        major_categories[currMajor].append(templist)
                        i += 6
                        if lines[i] in major_categories.keys(): #check if we have looped through all the subcategories
                            break
                    continue                       
            i += 1

    # print out each category
    # for item in major_categories:
    #     print(f'{item}: {major_categories[item]} \n')


    #TODO: normalize the units to a single unit. In the future, may want option to choose the unit. For now, normalize to per pound and to per head.
    #!* Units: 
        #!* What units are major? Head, CWT, etc.

    #* obtaining the conversion for weight to head
    #* conversion_cwt_to_head = major_categories["Stocker Purchase"][0][1]
    #* could possibly also care about buy/sell weight/price, but will leave out for now.

    major_categories["Buy Weight"] = ["Buy Weight", major_categories["Stocker Purchase"][0][1], yearVal]
    major_categories["Buy Price"] = ["Buy Price", major_categories["Stocker Purchase"][0][3], yearVal]
    major_categories["Sell Weight"] = ["Sell Weight", major_categories["Stocker"][0][2], yearVal]
    major_categories["Sell Price"] = ["Sell Price", major_categories["Stocker"][0][4], yearVal]

    # aggretating the subcategories
    for key in major_categories:
        summed_total_price = 0
        # subcategory unit conversion & sum
        if key in ["Stocker"]:
            major_categories[key] = [key, major_categories[key][0][5]]
        elif len(major_categories[key]) > 1: # for the case where the dict item stores values and not lists
            if not(isinstance(major_categories[key][0], list)): # skip over the different lists
                continue
            else:
                # check the unit and normalize. Normalize to CWT. Do so by converting with the stocker cwt purchase in mind.
                for j in range(len(major_categories[key])):
                    summed_total_price += major_categories[key][j][4]
                major_categories[key] = [key, summed_total_price]
        elif len(major_categories[key]) == 1:
            major_categories[key] = [key, major_categories[key][0][4]]     
        else: # for the case of non-convertable unit in major category
            continue

    major_categories["Profit"] = ["Profit", major_categories["Total Revenue"][1] - (major_categories["Total Variable Costs"][1] + major_categories["Total Fixed Costs"][1]), yearVal]
    


    # for item in major_categories:
    #     print(f'{item}: {major_categories[item]} \n')
    
    #TODO: sum all of the subcategories into the major category. 
    #* COMPLETED

    #TODO: create a dataframe for each row following the form: 
    #!* category, $/unit, item unit

    for key in major_categories:
        if major_categories[key]:
            items_names.append(major_categories[key][0])
            values.append(major_categories[key][1])
        else:
            items_names.append(key)
            values.append(None)
    
    df = pd.DataFrame({'Category': items_names,
                        'Value': values,
                    })
    
    df = df.round({'Value': 2})

    # print(df)

    return df
    
    #TODO: task 4: want to add all of the unit prices into a major csv file in the form:
    #! category, district 1 cost, district 2 cost, district 3 cost, etc.
    #! then, add to major csv for each year. We also care about the breakeven price. Figure how to incorporate that.
    #! potentially normalize to cwt??
    #! Find way to run file on each pdf file and add to a csv. If it fails, return some sort of error.

    #TODO: Once the data is in csv, get rid of weird units and replace with averages
    #! for categories that are more infrequent than not (stocker delivery)

directory_path = r'C:\Users\baoxi\Documents\TAMU\Fall_2024\RESEARCH_ML\Working\2019_2023'

# looping through each file
dataframes = []

for filename in os.listdir(directory_path):
    if filename.endswith(".pdf"):
        file_path = os.path.join(directory_path, filename)

        dataframes.append(get_df_from_file(filename))

# print(dataframes)

for df in dataframes:
    df.set_index('Category', inplace=True)

combined_df = pd.concat(dataframes, axis = 1, ignore_index=True)

combined_df.reset_index(inplace=True)

print(combined_df)

combined_df.to_csv(r'C:\Users\baoxi\Documents\TAMU\Fall_2024\RESEARCH_ML\Working\combined_data.csv',index=False) # header=0

# get_df_from_file("2023D11StockersWinter.pdf")