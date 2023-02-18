# EzDive
## A simple scuba logbook

#### Video Demo: 
#### Description:

I am a passionate scuba diver and thought that for my CS50 final project, I'd make a "simple" dive logging web-app. 
Dive-logging can be done with pen and paper in notebooks or using desktop/mobile apps such as 'Subsurface' (written by Linux founder Linus Torvald). Paper notebooks run out of pages, don't provide summary statistics (such as total dive time, maximum depth etc) and desktop/mobile apps often complicated things unecessarily.

EzDive is a bare-bones, "some-frills" dive log that gives you the essentials to track your progress and dives.

#### Project contents/Files:
##### app.py
The python file that runs the flask backend. 

#### helpers.py
Python file that contains helpers functions to de-clutter the main app.py file. 
Examples of helper functions include functions for SQL queries, flask session scripts, a validator function to make sure empty dives are not created and a "check dive counter". The check dive counter is explained below in the design choices section.

#### Files in /templates
These files form the backbone of the dive logging app. 

##### Index.html - the start page. 
If a user is logged in, it will show a table of all logged dives listing the dive ID, the date of the dive, the location of the dive, the maximum depth reached, the dive time and the buddy that was along for the fun. Clicking on the view button will bring up the complete entry for that dive (and also where entries can be deleted or edited).

##### Login.html, register.html, apology.html
If a user is not logged in, the login page will appear. There are also links to register an account. Appology.html will show an error message if something went wrong with the web-app (such as trying to login with no entered information)

##### new.html and edit.html
This is the meat and bones of the app. A user can enter a dive and log a number of parameters such as the location, date, time in, what tanks were used, starting and end pressures (used to calculate the respiratory minute volume - how much gas was consumed per minute) and notes where one can write about the dive. 

##### entry.html
This page shows the contents of what was entered in the dive in a simple table. 

#### Design choices
EzDive offers a number of good to have features and limits others. For instance the app features no visually striking designs, images or fancy graphics. This is intentional. I wanted a responsive, easy to use app that would let me enter information quickly and in a logical manner. Graphics or images would have provided no functional benefit to the app. (This is a long-winded way of saying that I do not enjoy front-end dev work and prefer back-end. :P)

One of the features that falls into the "frills" category of EzDive is the inbuilt respiratory minute volume (RMV) calculator. This is a handy statistic that will tell you how much gas you breathe underwater. This is crucial for dive planning so you know how long you can stay underwater with a given tank. I didn't want to store this information in the SQL database for two reasons. One: it is annoying to calculate this information by hand and then enter it into the app. It defeats the purpose of an app that makes your life easier. And two: If the dive information needs to be edited, one would have to also re-calculate this information. 

Using javascript, the app fetches the size of the tank(s) used for the dive (hard-coded), and using the total dive time, average depth and starting and ending pressures of the tank, calculates the RMV. This way one can easily track the RMV for different dives. In future, the app could be expanded to show how the RMV of a diver changes over time.

Another "frills" feature of EzDive is that if one selects either a dry-suit or wet-suit dive, the respective field for suit choice becomes visible. So if one dives a drysuit, the wetsuit parameter can no longer be entered but instead dry-suit undergarment can be entered. This was coded in javascript. 

As mentioned before, the app also contains a dive auto-incrementer. Sometimes you want to enter training dives into your log but then you lose track of what dive number you're up to. This function checks if the last entry was a string or a number. If it was a number, it auto-increments the dive number. If the last entry was a string, it recursively checks when the last log entry was a number and then increments that number. This way you can log your training dives but still keep easy track of your actual dive count.

#### Planned updates
Due to time constrains, some features could not be implemented. I wanted to include a summary page for each individual diver to show them the total number of dives they have done, the number of "unlogged" training dives, the maximum depth, longest dive and total dive time.
This feature could also include some simple graphs to show this data graphically.