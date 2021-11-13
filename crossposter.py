import pytumblr
import json
from bs4 import BeautifulSoup
from urllib.request import urlopen

with open('keys.json') as f:
    keys=json.load(f)

#keys we are gonna need to post on tumblr later

site=urlopen('https://sigmaleph.dreamwidth.org/')
soup=BeautifulSoup(site.read(),'html.parser')
wrappers=soup.find_all('div', attrs={'class':'entry-wrapper'})
#entry-wrapper divs contain the entries we want
with open('last_id.txt') as f:
    last_id=f.read()
#this stores the id of the most recent crossposted entry

entry_data=[]
for wrapper in wrappers:
    
    entry=wrapper.find('div',attrs={'class':'entry'}) #the div that contains everything else
    
    entry_id=entry['id']
    if entry_id==last_id: #stops the loop when i find a post i already crossposted
        break
        
    entry_title=entry.find('h3', attrs={'class':'entry-title'})
    title=entry_title.text
    if title=="(no subject)":
        title=''
    link=entry_title.find('a')['href']
    
    content=entry.find('div', attrs={'class':'entry-content'}).decode(formatter="html")
    content=content.replace('\n','') #formatting issue, kind of a hack
    
    taglist=['dreamwidth crosspost'] #this tag should go on all crossposts regardless of other tags
    tagdiv=entry.find('div', attrs={'class':'tag'}) #if this div exists, there are further tags
    if tagdiv!=None:
        alist=tagdiv.find_all('a')
        for a in alist:
            taglist.append(a.text)
            
    entry_data.append({'id':entry_id,
                      'title':title,
                      'link':link,
                      'content':content,
                      'tags':taglist})

#now to handle archiving

to_post=[]
for entry in entry_data:
    if 'dnxp' not in entry['tags']:
        to_post.append(entry)
    tagtext=''
    for tag in entry['tags']:
        if tag!='dreamwidth crosspost':
            tagtext=tagtext+tag+', '
    tagtext=tagtext[0:-2]
    outtext='id: '+entry['id']+'\n'+'title: '+entry['title']+'\n'+'content:\n'+entry['content']+'\n'+'tags: '+tagtext
    with open('archive/'+entry['id']+'.txt','w') as f:
        f.write(outtext)

entry_data=to_post #this makes sure the entries posted are the ones that don't have the dnxp tag

#we now have all the data we need conveniently organised, let's post to tumblr!

client = pytumblr.TumblrRestClient(keys['oauth consumer key'], keys['secret key'], keys['token'], keys['token_secret'])

entry_data.reverse() #as the list is in reverse chronological order, i reverse it so earlier elements are queued first
try:
    for entry in entry_data:
        client.create_text('sigmaleph', 
                       state='queue', 
                       title=entry['title'], 
                       format='html', 
                       body=entry['content']+'<a href="{0}">[original post]</a>'.format(entry['link']), 
                      tags=entry['tags'])
    latest_id=entry_data[-1]['id']
    with open('last_id.txt','w') as f: 
        f.write(latest_id)
    #this should not execute if there's an error, because it will mark entries as already crossposted
except ConnectionError:
    print("Check your connection")

