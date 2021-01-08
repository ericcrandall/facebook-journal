#!/usr/local/bin/python3


# -*- coding: utf-8 -*-

# Each your_posts.json has 5 components:

# * timestamp - timestamp
# * attachments - associated links or photos
# * data - the post itself
# * title - "Eric Posted in Washington Place" or "Eric updated his status"
# * tags - People that you tagged


# Some code borrowed from: https://www.dataquest.io/blog/analyze-facebook-data-python/
# https://stackoverflow.com/questions/13784192/creating-an-empty-pandas-dataframe-then-filling-it
# https://stackoverflow.com/questions/23794082/pandas-groupby-and-join-lists
# https://datascience.stackexchange.com/questions/31007/merging-information-of-rows-with-the-same-date
#https://help.dayoneapp.com/en/articles/435871-command-line-interface-cli
# Facebook outputs text incorrectly coded as UTF-8 as described [here](https://stackoverflow.com/questions/50008296/facebook-json-badly-encoded) 
# (it's a mojibake).
 
   
# setup
import sys
import pandas as pd
import subprocess


# Usage
if len(sys.argv) < 4:
   print("")
   print("This python script will convert your Facebook posts into a tab-delimited file [date<\t>title+post_text+tags+links<\t>photo_uri] and import it into the Day One journaling software.")
   print("Usage: facebook_to_journal.py -infile <infile> -outfile <outfile> -DayOneJournal <journal> -freq <aggregation frequency>")
   print("-infile: path/to/your_posts.json")
   print("-outfile: path and name for tab-delimited output (.tsv)")
   print("-DayOneJournal: Name of journal that will receive import in DayOne. This option is required for DayOne import to occur.")
   print("-freq: Frequency over which to aggregate posts in output. e.g. '1H' is hourly; '1S' would remove aggregation See https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases")
   print("The Day One command line tool (dayone2) must be installed for Day One import to work. See https://help.dayoneapp.com/en/articles/435871-command-line-interface-cli")
   sys.exit()

#Parse arguments
for i in range(len(sys.argv)):
    if sys.argv[i] == "-infile":
        infile = sys.argv[i+1]
    elif sys.argv[i] == "-outfile":
        outfile = sys.argv[i+1]
    elif sys.argv[i] == "-DayOneJournal":
        journal = sys.argv[i+1]
    elif sys.argv[i] == "-freq":
        freq = sys.argv[i+1]
    else:
        journal = "Facebook2"
        freq = "1H"
        outfile = "facebook_to_journal.tsv"
        infile = 'posts/your_posts_1.json'



#initialize empty list
output = []
#read in the json data
df = pd.read_json(infile)

# rename the timestamp column, and convert it
df.rename(columns={'timestamp': 'date'}, inplace=True)
pd.to_datetime(df['date'])
df.date.dt.strftime('%Y-%m-%d %H:%M')

# loop through posts, extracting text, tags and attachments (links and photos)
for post in range((len(df.data) - 1)):
   
   
    
    photo_uri = ""
    date = df.date[post]
    title = df.title[post]
    tags = df.tags[post]
    
    print(post, date)
    
    #un-scramble the mojibake of poorly encoded post text. Handle several errors resulting from posts that don't have any text.
    try:
        post_text = df.data[post][0]['post'].encode('latin1').decode('utf-8')
        
    except KeyError:
        post_text = ""
    except IndexError:
        post_text = ""
    except TypeError:
         post_text = ""
         
         
    #handle the attachment, checking first to see if it is a link, then checking if it is a photo, or nothing
    try:
        link_text = df.attachments[post][0]['data'][0]['external_context']['url']
    except KeyError:
        try: 
            link_text = ""
            photo_uri = df.attachments[post][0]['data'][0]['media']['uri']
        except KeyError:
            link_text = ""
    except IndexError:
       link_text = ""
    except TypeError:
         link_text = ""

    # handle the tags, if any
    if type(tags) is float:
        tag_text = ""
    else:
        tag_text = "Tagged " + ", ".join(tags)
            
    # paste together the title, text, tags and links into a single string
    try:
        text = title + "\n" +  post_text  + "\n" + tag_text + "\n" + link_text 
    except TypeError:
        text = post_text  + "\n" + tag_text + "\n" + link_text 
    
    # append dates, text and photo links into the list
    output.append([date, text, photo_uri])
    
    # add the data to DayOne using the dayone2 unix executable
    if photo_uri=='':
        command = """/usr/local/bin/dayone2 -j '%s' -d '%s' new '%s' """ % (journal, date, text)
    else:
        command = """/usr/local/bin/dayone2 -j '%s' -d '%s' -p %s -- new '%s'""" % (journal, date, photo_uri, text)
    
    subprocess.run(command, shell = True)

    
    
#convert the list to a data frame
output_df = pd.DataFrame(output, columns=['date', 'text', 'photo'])

#Aggregate entries that have the same date and time. 
bydate_df = output_df.groupby(pd.Grouper(key='date',freq= freq )).agg({'text': ' '.join, 'photo': ' '.join})
# Delete rows from the aggregation that don't have any entries
nan_value = float("NaN")
bydate_df.replace("", nan_value, inplace = True)
bydate_df.dropna(how='all', inplace = True)



#write the output
bydate_df.to_csv(outfile, sep = "\t")
    







#%%