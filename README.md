# Ultrabot

A bot designed to organize your server. Moderation, Utility, and Fun, all wrapped up into one, lightweight bot.

## Foreword

Please note that Ultrabot is specially designed to cater one server at a time. Make sure that you secure the bot to only one server. However, feel free to host multiple instances at once for multiple servers.

## Setting up the Server

Ultrabot functions with a specific server structure in mind.  First of all, we're going to make sure that your server is in accordance with that.

### Channels

There are a couple of channels that you are *required* to have in order to ensure that Ultrabot works.
* A general channel.
* A code-help/code-mentoring channel (doesn't have to be named that).
* A welcome channel.
* A verification channel.
* An empty category for roulette games.
* At least one voice channel.

### Roles
This part is super important! It ensures that the bot is able to verify users, then give them access to your server. Additionally, the bot also has a mute command, for which there must be a 'mute' role.

There are two types of channels you should consider:

* Public - Channels that everyone who joins the server can see.
* Private - Channels that only the verified can see.
* Temp - Channels only viewable by those who have joined but not verified.

I suggest making the Welcome and Announcements Public, and all other channels Private.
The only exception is the Verification channel, which I named 'verify' in my server, which should be your only Temp channel.

In order to achieve this, do the following:
* Put Announcements and Welcome in their own category. Don't do anything to that category, so that everyone can see it.
* Make a new category. Inside of that category, put the verification channel. This is going to be a little weird, but what you're going to want to do is make it so that @everyone can see that channel, but anyone with the Mute and Verified roles cannot see it. What this basically does is that it allows you to make sure that Verified people don't 're-verify', so to speak.
* For every other channel/category, text and voice included, make it so that only those who have the Mute or Verified roles can see it, but @everyone cannot.

It doesn't matter who it is. Even mods need to have the verified role. The verified role defines the control structure of channels. If you give someone the mod role, but not verified, they may not be able to see the channels unless they have administrator perms. For ease of access, I suggest making additional roles to strengthen the chain of command, while ensuring that all verified members have the verified role.

Note that the moderator commands require the permissions that you would need if you were to normally do such a thing.

That's just about it when it comes to configuring roles! Onto the next part!


## Getting the Proper Resources

Ultrabot makes use of various resources in exchange for the ability to perform a plethora of useless tasks. In order to be able to use these resources, you're going to need to obtain a couple of credentials. Fun!

### Reddit

Ultrabot features some premade reddit scrapers, including two meme scrapers. In order for Ultrabot to be able to work its magic, you're going to need a Reddit API Key, which can be done by making a developer application. Sound complicated? It's really not! Let's go through how to do this.

Let's start by going to the reddit developer page. That can be found [here](https://ssl.reddit.com/prefs/apps/). Go, log in, and create an app. This app should be classified as a script, and you can name it whatever you want. Once you do this, you should end up on a page with the information of the app, including the client secret and client id. Keep this page open, as you will need these for the setup of the script.

### Youtube API

The music commands in Ultrabot retrieve a lot of information in order to serve up the preview. This is all done with the Youtube Data API. You don't need to worry about the code, but you still need a key in order to be able to access this data. Let's go get you one! Visit the page [here](https://developers.google.com/youtube/v3/getting-started). It should have detailed instructions on how to get your data key. Save the API key here as well, or just keep the page open, so that it is handy for script setup.

### Making a Mail Bot

This part is pretty simple! Just make a google account without 2FA. After doing so, go to your account settings and turn on access from less secure apps. Although it seems scary, all this does is that it allows the bot to be able to log into your bot account if it has the proper credentials.

### Making a Discord Bot Account

For the bot to run, it needs to actually log into a container account. To do that, go the [discord developer portal](https://discordapp.com/developers/applications/) and create an application by clicking on 'New Application'. Then, click on the 'Bot' tab. Once there, create a bot by clicking 'Add Bot', Name the bot whatever you want, and the bot should generate. Along with the bot, a token should be generated. Keep the page open, as you will need to copy this token into the config file.


## Setting up Persistent Storage

Another cool thing about Ultrabot is that it has persistent storage! This may seem trivial, but persistent storage between deployments is a hard thing to do! Lucky for us,  Google's Firebase makes things simpler than normal. Let's get right on that!

Start by going [here](https://firebase.google.com/). Log in with your primary email address, and then go to the console. Once there, create a project, which can be titled whatever you want. Remember, the only reason we're using Firebase is for Firestore, their database system. This part is going to be a little tricky, because it's time for us to establish the firebase file structure.

Begin by going to the database tab, which is in the 'develop' section. Once there, create a *Firestore* database. I cannot stress this enough. We don't want the realtime database, we want firestore. Your database should be in locked mode.

Let's make sure that nobody can access the data in your database except for you. Go to the 'rules' tab of your database.  You're going to want to clear out whatever is in the rules section, and replace it with the following.

```
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```
This completely restricts database access for everyone except people using a json key... which we're going to obtain in a bit! Before that, let's establish the file structure.

There are five collections that you're going to have to create, or 'start':
* blacklist
* playlists
* daily
* leaderboard
* timeouts

When starting each collection, firestore will try to get you to make a document to populate the database. Make the document id the name of the collection, and don't add any fields. Once you do this for five repetitions, you should be done with the file structure. Make sure that the names of the collections are *verbatim* what I've written above.

We're almost done with this! The last step is obtaining a json key. To do this, go to the settings tab, and click on the project settings option. Go to the service accounts tab, and scroll down. You're going to want to generate a new private key. What this does is that you will be given a json file. This json file allows Ultrabot to access your database. Neat!


## Setting up the Script

This isn't too hard! First of all, you're going to want to clone/fork the repository. Once you do that, there should be a file called info.py. Make a copy of that, name it secret.py, and fill in the appropriate information. That's it! You're done setting up the script! Now to deploy it...

## Running the bot

Ultrabot is made with it running on heroku in mind. If you don't want to run Ultrabot on Heroku, all you need is the Ultrabot.py, pokarray.py, and secret.py files. Make sure that you delete lines 1052-1081, as well as lines 1111-1140 in the caes you would like to use your own server. There are some other things too, but if you're using your own server you can probably figure out the rest of the setup by reading the rest of this guide.

Back to heroku! First of all, make sure that you have the cloned repo along with the secret.py all in a new repository on your own github. Make sure that none of the files are in the gitignore!

### Setting up a Heroku App

Some of you might still be scratching your heads as to what Heroku is. In a nutshell, Heroku is a service that allows you to deploy web applications online, and it has a free tier. The cool thing about Heroku is that you can run non-web apps as well with a couple of tweaks to the way the app is set up. Let's get right on that!

Go [here](https://www.heroku.com) and create a new Heroku account. Once that's been done, create a new app, which can be called whatever you want, and can be hosted wherever you want. The only thing left is configuring the settings of this project.

### Configuring the Buildpacks

Go into the settings of your Heroku Application. Scroll down, and there should be a section where you can add buildpacks. You're going to add four buildpacks. For each buildpack, it will ask you for a URL. Use the following URLs:
* heroku/python
* heroku/jvm
* https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
* https://github.com/xrisk/heroku-opus.git


And that's just about it! Go to the Deploy Tab, connect your Github Account, select the repo you put the Ultrabot files in, and deploy the application! Like magic, everything should start working, and the bot should join your server. Sweet!

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
