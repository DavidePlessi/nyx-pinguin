Authorization
How to authorize for requests that require server authorization.
Some requests will require you to authorize because the retrieved data is sensitive. Every server has an API key that only members with admin or manage server permissions can access. The API key can be shown and refreshed with the /apikey command in your server. If you accidentally shared your servers API key with someone that you don't trust, you should immediately refresh the API key to prevent any abuse.

The authorization is done by adding a header to your request with the name "Authorization" and the API key as the value.

GET
https://raid-helper.xyz/api/v4/events/EVENTID
Fetch the full data of a single event. Does not require authorization!
This request will return you the full data of the specified event. No authorization is required. Because this is a GET request it can be easily accessed via the browser. Here is an example. If you wish to view the JSON in a structured way inside your browser, consider installing a chrome extension like JSONVue to format the data properly for you.
Request Structure

Headers

Authorization<apikey> - Your servers api key which you can get and refresh via /apikey.
Response Structure

Body

id<string> - The message id of this event.
serverId<string> - The server id of this event.
leaderId<string> - The user id of this events leader.
leaderName<string>- The name of events leader.
coLeaders<array of objects> - The co-leaders of this event. Each entry is an object with the user id (id) and name (name) of a co-leader.
channelId<string> - This events channel id.
channelName<string> - This events channel name.
channelType<string> - The type of this events channel.
templateId<string> - The id of this events template.
templateEmoteId<string> - The emote id of the emote used to represent the template of this event.
title<string> - The event title.
description<string> - The event description.
startTime<number> - The unix timestamp of when this event will start.
endTime<number> - The unix timestamp of when this event will end.
closingTime<number> - The unix timestamp of when this event will close and deny further sign-ups.
date<string> - The raw date string of when this event will start.
time<string> - The raw time string of when this event will start.
advancedSettings<object> - The advanced settings for this event.
classes<array of objects> - The classes that are applied to this event.
roles<array of objects> - The roles that are applied to this event.
signUps<array of objects> - The current sign-ups on this event.
lastUpdated<number> - The unix timestamp of when this event was updated last.
softresId<string> - The softres id attached to this event.
color<string> - The current embed color in RGB format.

GET
https://raid-helper.xyz/api/v4/servers/SERVERID/events
Fetch general data of all events on your server.
This request will return an array of your posted events. The response will never contain more than 1000 events. If you have more than that please use the Page header to navigate to subsequent pages. The current page and event count as well as the overall pages and event count are returned in the body.
Request Structure

Headers

Authorization<apikey> - Your servers api key which you can get and refresh via /apikey.
Page<number> - The page number to return. Maximum of 1000 events per page.
IncludeSignUps<boolean> - Whether to include the Sign-Ups of each event in the response.
ChannelFilter<string> - The channel id to filter by. All channels are included if none provided.
StartTimeFilter<number> - The unix timestamp of the earliest event to include.
EndTimeFilter<number> - The unix timestamp of the latest event to include.
Response Structure

Body

pages<number> - The amount of pages available.
currentPage<number> - The page number of the response.
eventCountOverall<number> - The overall event count on your server.
eventCountTransmitted<number> - The amount of events in this response.
postedEvents<array of objects> - Contains the objects of all posted events on this server.

GET
https://raid-helper.xyz/api/v4/servers/SERVERID/scheduledevents
Fetch general data of all scheduled events on your server.
This request will return an array of your scheduled events.
Request Structure

Headers

Authorization<apikey> - Your servers api key which you can get and refresh via /apikey.
Response Structure

Body

scheduledEvents<array of objects> - Contains the objects of all scheduled and recurring events on this server.

GET
https://raid-helper.xyz/api/v4/servers/SERVERID/attendance
Fetch the attendance statistics for your server.
This request is used to fetch the attendance statistics for your server. Only closed events are included in the attendance calculation. Roles named Bench, Late, Tentative, Absence, Maybe and Declined are not included in the calculation. You can narrow the query down by the timeframe viewed, the channels the events are in and by the attendance tag used on the events.
Request Structure

Headers

Authorization<apikey> - Your servers api key which you can get and refresh via /apikey.
Content-Typeapplication/json; charset=utf-8 - Defines the content type.
TagFilter<string> - The attendance tags to filter by. All tags are included if none provided.
ChannelFilter<string> - The channel ids to filter by. All channels are included if none provided.
TimeFilterStart<number> - The unix timestamp of the earliest event to include.
TimeFilterEnd<number> - The unix timestamp of the latest event to include.
Response Structure

Body

tagFilter<array of strings> - The attendance tags to filter by. Default is to include all tags that are not set to false.
channelFilter<array of strings> - The channelIds to filter by. default is to include all event channels.
timeFilterStart<number> - The unix timestamp of the earliest event to include.
timeFilterEnd<number> - The unix timestamp of the latest event to include.
result<array of objects> - the array containing the attendance statistics for the queried events.