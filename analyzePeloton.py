import requests
import csv
import json


from datetime import datetime
# from datetime import timezone
# from datetime import date

import matplotlib.pyplot as plt
import matplotlib.dates as mdates 
import pandas as pd

s = requests.Session()
payload = {'username_or_email':'<insert username>', 'password':'<insert password>'}
xx = s.post('https://api.onepeloton.com/auth/login', json=payload)

'''
The following script has been a way for me to play around with my own Peloton fitness data. My family's Peloton bicycle and my most recent download of the Peloton Digital Application
has been motivating my workouts during this period of social distancing. As a data person, I have been fascinated by the amount of data amassed, shared and available for visualization 
while working out. 
At any given moment, there are people across the world riding with me, running with or stretching with me. I know when a friend has a taken a new class and I know if I have beat 
my record from the previous day. How does Peloton do it? What is the data structure underlying and powering the app, the tablet, the website, the notifications? 

I must give credit to 
https://github.com/geudrik/peloton-api
https://rdrr.io/github/elliotpalmer/pelotonr/api/

where I found the API endpoints and could have used either library. But the best way to explore data is to struggle and wrangle with it myself while at the same time refamiliarizing myself 
with Python, Pandas and data manipulation. 

From what I have found, the API fields are clear, data is consistent and clear. 
There are some funny quirks which seem to be a result from Peloton's growth- starting with cycling and movement to classes of all types 
1. Nesting of data within 'ride' json field even for a "running" class, or 
2. the total_output only included for cycling classes instead of creating a more standard way to calculate total output across all types of classes)
3. 'total_leaderboard' on top level of json also often empty.

I hope to continue to explore and document more of the fields and explain what they mean to better think of my workouts in the form of data. 

'''


#########################################
#####            Profile           ######
#########################################

# meContent = s.get('https://api.onepeloton.com/api/me').json()

###### KEY NAMES 
# [u'username', u'last_name', u'is_demo', u'weight', u'is_profile_private', u'cycling_ftp_workout_id', u'created_country', u'cycling_workout_ftp', u'height', u'is_provisional', u'cycling_ftp', u'id', 
# u'total_pending_followers', u'block_explicit', u'facebook_access_token', u'customized_max_heart_rate', u'is_strava_authenticated', u'obfuscated_email', u'hardware_settings', u'is_complete_profile', u'instructor_id', u'v1_referrals_made', 
# u'last_workout_at', u'location', u'is_internal_beta_tester', u'facebook_id', u'cycling_ftp_source', u'has_active_digital_subscription', u'email', u'phone_number', u'contract_agreements', u'middle_initial', u'quick_hits', 
# u'external_music_auth_list', u'first_name', u'card_expires_at', u'birthday', u'has_signed_waiver', u'customized_heart_rate_zones', u'referrals_made', u'is_external_beta_tester', 
# u'paired_devices', u'total_pedaling_metric_workouts', u'total_workouts', u'default_max_heart_rate', u'name', u'is_fitbit_authenticated', u'has_active_device_subscription', u'gender', 
# u'created_at', u'workout_counts', u'total_non_pedaling_metric_workouts', u'member_groups', u'default_heart_rate_zones', u'image_url', u'total_following', u'estimated_cycling_ftp', u'can_charge', u'total_followers']

## print meContent['id'] 
userid = "c3ff56ef4c834f8eb682e724494e1d27" # meContent['id']

#########################################
#####            Workouts          ######
#########################################


# The workouts endpoint truncates 20 to page however the workoutsFullEndpoint passes a parameter that allows a larger limit. 
# It was easier to hack this and set a large limit (which I knew based on my application dashboard)
workoutsPagingEndpoint = 'https://api.onepeloton.com/api/user/%s/workouts' % (userid)
workoutsFullEndpoint = 'https://api.onepeloton.com/api/user/%s/workouts?joins=ride&limit=%s' % (userid, 200) #The number should be changed - but just putting in limit that I know is past the total number of workouts

workouts = s.get(workoutsFullEndpoint).json()

###### KEY NAMES 
# [u'count', u'summary', u'page_count', u'show_next', u'sort_by', u'show_previous', u'next', u'limit', u'aggregate_stats', u'total', u'data', u'page']
# Need to find way to loop through all the page count, 'page_count' shows total number of pages and 'page' is the page that you are on...

# Data of workout is found inside 'data' key
workoutData = workouts['data']

# In order to avoid running through endpoint - just grab a list of workoutId to use for later endpoint
listOfWorkoutIds = []
for workout in workoutData:
# Sample workout
# {u'workout_type': u'class', u'total_work': 0.0, u'is_total_work_personal_record': False, u'device_type': u'iPhone', u'timezone': u'America/New_York', u'device_time_created_at': 1586800817, u'id': u'8b83bece729648e0a8dc2671c66a3b66', u'fitbit_id': None, u'peloton_id': u'84360c083b714f5d93f937d4d07d2102', u'user_id': u'c3ff56ef4c834f8eb682e724494e1d27', u'title': None, u'has_leaderboard_metrics': False, u'has_pedaling_metrics': False, u'platform': u'iOS_app', u'metrics_type': None, u'fitness_discipline': u'stretching', u'status': u'COMPLETE', u'start_time': 1586815306, u'name': u'Stretching Workout', u'strava_id': None, u'created': 1586815217, u'created_at': 1586815217, u'end_time': 1586815896}
#	print workout['total_work'] -- Only cycling classes have total_work when looping through, all other data is inside the 'ride'
#	print workout['fitness_discipline']
	workoutId = workout['id']

	# Help to find specific Id's if need to test different categories
	# if workout['fitness_discipline'] in ['cycling', 'running']:
	# 	# do something
	# else:
	# 	# do something else
	listOfWorkoutIds.append(workoutId)

## Get Class details for an individual workout. For example (Stretching Class example): 8b83bece729648e0a8dc2671c66a3b66, Walking class: 3d4e2277bca743cfa839a7ffae6ff2ac
## This is the workout of a person for a particular class
## This has an associated peleton_id (To what is this associated?)

## The finalData list is a list of dictionaries to say output to csv if want to chart elsewhere (outside of python)
finalData = []

#########################################
#####      Specific Workout        ######
#########################################

workoutDetailEndpoint = 'https://api.onepeloton.com/api/workout/%s'

# [u'workout_type', u'total_work', u'is_total_work_personal_record', u'device_type', u'total_leaderboard_users', u'timezone', u'leaderboard_rank', u'device_time_created_at', 
# u'id', u'fitbit_id', u'peloton_id', u'user_id', u'title', u'has_leaderboard_metrics', u'has_pedaling_metrics', u'platform', u'metrics_type', u'achievement_templates', 
# u'fitness_discipline', u'status', u'device_type_display_name', u'start_time', u'name', u'strava_id', u'created', u'created_at', u'ftp_info', u'end_time', u'ride']
## Inside ride is where the data for the workout lives - Question: the data for the class changes- so is the workoutid unique and/or does the meta class data change 


#########################################
#####     Performance Graph        ######
#########################################

## Performance Graph endpoint
workoutPerformanceEndpoint = 'https://api.onepeloton.com/api/workout/%s/performance_graph' 

###### KEY NAMES 
# [u'is_class_plan_shown', u'splits_data', u'location_data', u'average_summaries', u'metrics', u'segment_list', u'duration', u'is_location_data_accurate', u'has_apple_watch_metrics', u'summaries', u'seconds_since_pedaling_start']
# workoutPerformanceDetail['average_summaries'] Example:
# [{u'display_name': u'Avg Pace', u'slug': u'avg_pace', u'value': 16.22, u'display_unit': u'min/mi'}, {u'display_name': u'Avg Speed', u'slug': u'avg_speed', u'value': 3.7, u'display_unit': u'mph'}]
# workoutPerformanceDetail['summaries'] Example
# [{u'display_name': u'Distance', u'slug': u'distance', u'value': 1.23, u'display_unit': u'mi'}, {u'display_name': u'Elevation', u'slug': u'elevation', u'value': 74, u'display_unit': u'ft'}, {u'display_name': u'Calories', u'slug': u'calories', u'value': 146, u'display_unit': u'kcal'}]





# Loop through workoutIds in the list to grab some meta data on workout itself
for wkid in listOfWorkoutIds:

	workoutDetail = s.get(workoutDetailEndpoint % (wkid)).json()
	if workoutDetail['fitness_discipline'] != 'meditation':

		workoutDict = dict(workoutId=workoutDetail['id'], fitness_discipline = workoutDetail['fitness_discipline'], created_at = datetime.fromtimestamp(workoutDetail['created_at']))
		# Data fields I plan to use now:
		# workoutDetail['id']
		# workoutDetail['fitness_discipline']
		# workoutDetail['total_leaderboard_users']
		# workoutDetail['leaderboard_rank']
		# workoutDetail['created_at']
		# workoutDetail['start_time']

		workoutPerformanceDetail = s.get(workoutPerformanceEndpoint % (wkid)).json()
		# Calories are found in a list of dicts with a display name, slug and value (See sample above)
		calorieOutput = [i for i in workoutPerformanceDetail['summaries'] if (i['slug'] == 'calories')][0]['value']
		workoutDict['calories'] = calorieOutput
		finalData.append(workoutDict)
	else:
		pass #Dont care for meditation classes at this point in time- mostly concerned about active fitness

# Convert to Pandas dataframe
df = pd.DataFrame(finalData)  

# Task 1: Plot Calories by Day

# Create pretty Date column
df['Date'] = df.apply(lambda row: row.created_at.date(), axis=1)
df2 = df.groupby("Date", as_index=False).calories.sum()

df2['Date'] = pd.to_datetime(df2.Date) #, format='%Y%m%d'
df2['DateName'] = df2.Date.apply(lambda x: x.strftime('%B %d, %Y'))

df2.sort_values(by=['Date'], inplace=True, ascending=True)

# fig, ax = plt.subplots()
# ax.plot('Date', 'calories', data=df2)

ax = df2.plot(x ='Date', y='calories', kind = 'bar', xticks=df.index)
ax.set_xticklabels(df2.DateName)

# df['Daily Calories']= df.apply(lambda row: row.a + row.b, axis=1)

#set ticks every week
# df2.xaxis.set_major_locator(mdates.WeekdayLocator())
#set major ticks format
# df2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

plt.show()





# Perhaps to output to a csv at a later point to run through other tools: 
# fields = ['peloton_id', 'user_id', 'title', 'fitness_discipline', 'total_work', 'total_leaderboard_users', 'leaderboard_rank']
# # , 'total_workouts', 'difficulty_rating_avg'

# # name of csv file
# filename = "MyPeletonData.csv"
# with open(filename, 'w') as csvfile:
# 	writer = csv.DictWriter(csvfile, fieldnames = fields)
# 	writer.writeheader()
# 	writer.writerows(mydict)
