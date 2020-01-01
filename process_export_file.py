from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import random
import plotly.io as pio
margin_dict = dict(l=0, r=0, t=1, b=0)

for_year = 2019

def chat_unique_count(chat_series):
       return chat_series.nunique()


def newline_status(chat_line): 
    '''
    Function to process multiline messages
    '''
    split_msg = chat_line.split(": ")
    date_and_phone = split_msg[0].split(' - +')
    if len(split_msg) > 1 and len(date_and_phone)>1: ##Default
        return 1 ## Standard
    else: ##Handle Multilines, New Members
        #New Members
        date_and_phone = split_msg[0].split(' - +')
        if len(date_and_phone) > 1:
            return 2 #New Member
        else:
            return 3 #Message Extension

def process_chat_text_export(chat_file):
    '''
    convert export chat text file to a feature arrays
    '''
    msg_vector = []
    new_members = []
    other_events = []
    phone, message, time_of_chat = None,'',None
    for chat_line in chat_file:
        line_type = newline_status(chat_line)
        split_msg = chat_line.split(": ")
        date_and_phone = split_msg[0].split(' - +')
        if line_type == 1:
            if phone is not None:
                msg_vector.append([phone, time_of_chat,message])
            message = ": ".join(split_msg[1:])
            time_of_chat = datetime.strptime(date_and_phone[0].strip(), '%d/%m/%Y, %H:%M')
            phone = date_and_phone[1]
        elif line_type == 2:
            date_and_phone = split_msg[0].split(' - +')
            time_of_chat = datetime.strptime(date_and_phone[0].strip(), '%d/%m/%Y, %H:%M')
            if (len(date_and_phone) > 1) and ('added' in date_and_phone[1]):           
                admin_phone,new_member_phone = date_and_phone[1].split(' added ')
                new_members.append([admin_phone,new_member_phone,time_of_chat,'added'])
            else:
                if 'left' in date_and_phone[1]:
                    other_events.append([date_and_phone[1][:-6],time_of_chat,'left'])
                elif 'security code' in date_and_phone[1]:
                    other_events.append([date_and_phone[1][:-45],time_of_chat,'code'])
                elif 'icon' in date_and_phone[1]:
                    other_events.append([date_and_phone[1][:-27],time_of_chat,'icon'])
        elif line_type == 3:
                message += chat_line
        
    return  msg_vector,new_members,other_events

with open('ntech2.txt',encoding='utf8') as ff:
    wcc = ff.readlines()
    tmp_msg_vector,tmp_new_members,tmp_other_events = process_chat_text_export(wcc)

#Process Text Data
col_names = ['member_phone','activity_date','message']
df_other_events = pd.DataFrame(tmp_other_events,columns=col_names)
df_chat_messages_tmp = pd.DataFrame(tmp_msg_vector,columns=col_names)
df_chat_messages = df_chat_messages_tmp[df_chat_messages_tmp['activity_date'].dt.year == for_year].copy(deep=True)
df_chat_messages['word_count'] = df_chat_messages['message'].map(lambda x : len(x.split(' ')))
df_chat_messages['adj. word count'] = df_chat_messages['word_count'].map(lambda x : 500 if x > 500 else x )
df_chat_messages['has_link'] = df_chat_messages['message'].map(lambda x : 'Y' if '://' in x else 'N')
df_chat_messages['has_media'] = df_chat_messages['message'].map(lambda x : 'Y' if '<Media omitted>' in x else 'N')
df_chat_messages['activity_hour'] = df_chat_messages['activity_date'].dt.hour
df_chat_messages['activity_day'] = df_chat_messages['activity_date'].dt.weekday #monday is 0
df_chat_messages['activity_month'] = df_chat_messages['activity_date'].dt.month
df_chat_messages['activity_date_ext'] = df_chat_messages['activity_date'].apply(lambda x : x.replace(second=0, minute=0))
del df_chat_messages_tmp

#Top 20 users by activity
word_count_df = df_chat_messages.groupby(by=['member_phone']).agg({'word_count':['count']}).reset_index()
word_count_df.columns = ['member_phone','total_chats']
dss = word_count_df.sort_values(by=['total_chats'],ascending=False).head(20)
dss['member_phone'] = dss['member_phone'].map(lambda x : '+:'+x)
dss.to_csv('user_activity.csv')

#Top 10 Media activity by user
df_chat_messages[df_chat_messages.has_media=='Y'].groupby(by='member_phone')\
.count().reset_index()[['member_phone','has_media']].sort_values(by='has_media',ascending=False)\
.head(10).to_csv('has_media.csv')

#Top 10 URL activity by user
df_chat_messages[df_chat_messages.has_link=='Y'].groupby(by='member_phone')\
.count().reset_index()[['member_phone','has_link']].sort_values(by='has_link',ascending=False)\
.head(10).to_csv('has_url.csv')

#Activity by hour of day
df_chat_messages.groupby(by='activity_hour').count().reset_index()[['member_phone']].to_csv('activity_by_hour.csv')

#Chat activity by month
chat_activity_by_day_mnth = df_chat_messages.groupby(by=['activity_month'])\
                            .agg({'member_phone':['count',chat_unique_count]}).reset_index()
chat_activity_by_day_mnth.columns = ['activity_month','chat_count','unique_members']
chat_activity_by_day_mnth.to_csv('mnthchat.csv')

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize

stop_words = list(stopwords.words('english'))
addins = ['lmao','dey','https','http','media','ommitted','ommitted media','na','us','n''t','go','lol','see','something',\
    'know','still','let','well','much','make','sha','even','one']
stop_words.extend(addins)
#Word CLoud
#bcolor="#282D36"
bcolor="white"
text = ' '.join([x.lower().replace("\n", " ") for x in df_chat_messages['message'] if 'media omitted' not in x.lower()])
word_tokens = text.split(' ')#word_tokenize(text) 
filtered_sentence = [w for w in word_tokens if w not in stop_words and 'http' not in w]
wordcloud = WordCloud(max_font_size=80, max_words=100,background_color=bcolor,margin=0,\
                    width=800, height=400).generate(' '.join(filtered_sentence))
fig = plt.figure(frameon=False,facecolor=bcolor,figsize=(20,10))
plt.imshow(wordcloud)
plt.axis("off")
plt.savefig("wordcount.png",bbox_inches='tight',pad_inches=0.1,transparent=True,dpi=800)


df_new_members = pd.DataFrame(tmp_new_members,columns=['admin','member','add_date','comment'])

#Group Stats
group_stats = {
'total_chats':df_chat_messages['message'].count(),
'has_media':df_chat_messages[df_chat_messages['has_media']=='Y']['message'].count(),
'has_link':df_chat_messages[df_chat_messages['has_link']=='Y']['message'].count(),
'unique_contributors':len(df_chat_messages['member_phone'].unique()),
'exits': df_other_events[(df_other_events['message']=='left') & (df_other_events.activity_date.dt.year==for_year)]['message'].count(),
'new_members':df_new_members[df_new_members.add_date.dt.year == for_year].shape[0]
}

print(group_stats)