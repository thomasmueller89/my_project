# my_project
How to run:
Python main.py dataset.csv
Then enter your input line by line
I'll save you some time by saying this
so my 4nf doesn't work so when you are prompted to input the multivalued dependencies
just input exit and skip that part
the resulting sql queries will be put in the SQL.txt file


Flow of project:
1. We first go to our parser section to receive input from the user
2. With that input we go to the normalize section where we utilize the to_nf and a series of helper
    functions to help normalize the dataset
3. After normalization, we move to the generate sql section where I have two functions that help complete the process

To be up front, here is a list of things that don't work as I ran out of time:
In the main normalizer:
to_4nf had an error that i couldn't resolve in time
to_5nf since i didn't finish to_4nf
This means i can only normalize to BCNF
In the optional find the normalization level of the input dataset:
only is_1nf works, the rest were not implemented

Overall, I thought this was a really tough but fun project, especially doing it solo
I'm excited to talk with classmates about how it went for them!