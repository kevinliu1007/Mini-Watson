import nltk
import os
import sqlite3
import re
from nltk.parse import stanford
from nltk.tag.stanford import StanfordNERTagger


# find if the sentence you enter is a question or not
# if it is return the sub tree of SQ
def findQ(t):
    if t.height() == 2:
        return False, False
    if t.label() == "SQ":
        return True, t
    else:
        for things in t:
            (a, b) = findQ(things)
            if a:
                return True, things
        return False, False


# find if the sentence you enter is a question or not
# specifically a question with WH- in it
def findS(t):
    if t.height() == 2:
        return False
    if t.label() == "WHNP":
        return True
    else:
        for things in t:
            (a, b) = findQ(things)
            if a:
                return True
        return False


# find all the word with specific POS tag
def findPOS(t, p):
    temp = []
    for tokens in t.pos():
        (a, b) = tokens
        if b == p:
            temp.append(a)

    return temp


# classify genre of movie
def genre(x):
    return {
        "drama": "D",
        "romance": "R",
        "scienceF": "S",
        "comedy": "C",
        "action": "A",
        "horror": "H",
        "adventure": "V",
        "fiction": "F",
        "animated": "N",
        "history": "Y",
        "thriller": "T",
        "mystery": "M",
        "scary": "H"
    }.get(x, "")


# main question answering function
def qa(q):
    # set up environments
    # if on Mac use line below and comment out the other line
    # os.environ['JAVAHOME'] = "/System/Library/Frameworks/JavaVM.framework/Home"  # set to your java location
    # for windows if java env path not set, do following
    # os.environ['JAVAHOME'] = 'C:\\Program Files\\Java\\jre1.8.0_111\\bin' # set to your java location
    os.environ['STANFORD_PARSER'] = './parser'
    os.environ['STANFORD_MODELS'] = './parser'

    # load up Stanford Parser and NER tagger
    parser = stanford.StanfordParser(model_path='./parser/englishPCFG.ser.gz')
    st = StanfordNERTagger('./NER/english.all.3class.distsim.crf.ser.gz',
                           './NER/stanford-ner.jar')

    # assign question to a variable
    question = q

    # remove special character from question and tag using Stanford NER tagger
    sent = question
    sent = sent.replace("?", "")
    sent = sent.replace("\'", "")
    temp = sent.split()
    result = st.tag(temp)

    # parse out question into tree
    s = parser.raw_parse(question)

    # store the tree into a variable
    thing = []
    for things in s:
        thing = things

    # find all the NNP, NN, CD, JJS, JJR in the sentence
    NNP = findPOS(thing, "NNP")
    NN = findPOS(thing, "NN")
    CD = findPOS(thing, "CD")
    JJS = findPOS(thing, "JJS")
    JJR = findPOS(thing, "JJR")

    # set up variable for category
    movie = False
    music = False
    geo = False

    # split up the question into words
    sentence = question
    sentence = sentence.replace("?", "")
    sentence = sentence.replace("\'", "")
    bunch = sentence.split()

    # go through the words to see if special words exist
    # then categorize the question
    for eachthing in bunch:
        # to see if question asks movie related topics
        if (eachthing.lower() == "directed" or eachthing.lower() == "movie" or eachthing.lower() == "oscar" or
                eachthing.lower() == "film" or eachthing.lower() == "actor" or eachthing.lower() == "actress" or
                eachthing.lower() == "star" or eachthing.lower() == "director"):
            movie = True
        # to see if question asks music related topics
        elif (eachthing.lower() == "sings" or eachthing.lower() == "sing" or eachthing.lower() == "song" or
                eachthing.lower() == "songs" or eachthing.lower() == "album" or eachthing.lower() == "artist"):
            music = True
        # to see if question asks geo related topics
        elif (eachthing.lower() == "continent" or eachthing.lower() == "capital" or eachthing.lower() == "mountain" or
                eachthing.lower() == "ocean" or eachthing.lower() == "border"):
            geo = True

    # if more than one location occurred in question, more likely it is geo question
    loc = []
    for things in result:
        (a, b) = things
        if b == "LOCATION":
            loc.append(a)
    if len(loc) >= 2:
        geo = True

    # if still cannot classify the question, check other conditions
    if not geo and not music and not movie:

        # maybe it is asking "born" related question
        if "born" in bunch:
            persons = []
            locations = []
            # find the person
            for things in result:
                (a, b) = things
                if b == "PERSON":
                    persons.append(a)
            if not persons:
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP":
                        persons.append(a)

            # find the location
            for things in result:
                (a, b) = things
                if b == "LOCATION":
                    locations.append(a)

            # if asking where or when is a person born in
            if persons and not locations and not CD:
                conn1 = sqlite3.connect("./DB/music.db")
                conn2 = sqlite3.connect("./DB/oscar-movie_imdb.db")
                cur1 = conn1.cursor()
                cur2 = conn2.cursor()

                # query
                q1 = cur1.execute("Select * From Artist Where name Like \'%%%s%%\'" % persons[0])
                q2 = cur2.execute("Select * From Person Where name Like \'%%%s%%\'" % persons[0])

                musicP = q1.fetchone()
                movieP = q2.fetchone()

                if musicP:
                    if "Where" in bunch:
                        return str(musicP[1]) + " is born in " + str(musicP[2])
                    elif "When" in bunch:
                        return str(musicP[1]) + " is born in " + str(musicP[3])

                elif movieP:
                    if "Where" in bunch:
                        return str(movieP[1]) + " is born in " + str(movieP[2])
                    elif "When" in bunch:
                        return str(movieP[1]) + " is born in " + str(movieP[3])

            # if asking born in specific date
            elif CD:
                conn1 = sqlite3.connect("./DB/music.db")
                conn2 = sqlite3.connect("./DB/oscar-movie_imdb.db")
                cur1 = conn1.cursor()
                cur2 = conn2.cursor()

                # query
                q1 = cur1.execute("Select * From Artist Where name Like \'%%%s%%\' " % persons[0] +
                                  "and dateOfBirth Like \'%%%s%%\'" % CD[0])
                q2 = cur2.execute("Select * From Person Where name Like \'%%%s%%\' " % persons[0] +
                                  "and dob Like \'%%%s%%\' " % CD[0])

                musicP = q1.fetchone()
                movieP = q2.fetchone()

                if musicP:
                    return "Yes"
                elif movieP:
                    return "Yes"
                else:
                    return "No"

            # yes or no questions
            else:
                conn1 = sqlite3.connect("./DB/music.db")
                conn2 = sqlite3.connect("./DB/oscar-movie_imdb.db")
                cur1 = conn1.cursor()
                cur2 = conn2.cursor()

                # query
                q1 = cur1.execute("Select * From Artist Where name Like \'%%%s%%\' " % persons[0] +
                                  "and placeOfBith Like \'%%%s%%\'" % locations[0])
                q2 = cur2.execute("Select * From Person Where name Like \'%%%s%%\' " % persons[0] +
                                  "and pob Like \'%%%s%%\' " % locations[0])

                musicP = q1.fetchone()
                movieP = q2.fetchone()

                if musicP:
                    return "Yes"
                elif movieP:
                    return "Yes"
                else:
                    return "No"

    # if it is geo related questions
    if geo:
        conn = sqlite3.connect("./DB/WorldGeography.db")
        cur = conn.cursor()

        # if it is asking "-est" type of questions
        if JJS:
            # height related questions
            if "highest" in JJS or "tallest" in JJS:
                if "height" in bunch:
                    q = cur.execute("Select Height From Mountains Order by Height DESC Limit 1")
                    return "The highest mountain's height is " + str(q.fetchone()[0])
                elif "What" in bunch or "Which" in bunch:
                    q = cur.execute("Select Name From Mountains Order by Height DESC Limit 1")
                    return "The highest mountain is " + str(q.fetchone()[0])
                elif "Where" in bunch:
                    q = cur.execute("Select Continent From Continents Order by Highest DESC Limit 1")
                    return "The highest mountain is in " + str(q.fetchone()[0])
                elif "population" in bunch:
                    q = cur.execute("Select Name From Continents Order by Population DESC Limit 1")
                    return "The continent with the highest population is " + str(q.fetchone()[0])

            # depth related questions
            elif "deepest" in JJS:
                if "depth" in bunch:
                    q = cur.execute("Select Deepest From Seas Order by Deepest DESC Limit 1")
                    return "The depth of the deepest ocean is " + str(q.fetchone()[0])
                elif "What" in bunch or "Which" in bunch:
                    q = cur.execute("Select Ocean From Seas Order by Deepest DESC Limit 1")
                    return "The deepest ocean is " + str(q.fetchone()[0])

            # population or area related questions
            elif "biggest" in JJS:
                if "population" in bunch:
                    q = cur.execute("Select Name From Continents Order by Population DESC Limit 1")
                    conn.close()
                    return "The continent with the highest population is " + str(q.fetchone()[0])
                elif "area" in bunch:
                    q = cur.execute("Select Name From Continents Order by Area_KM2 DESC Limit 1")
                    return "The continent with the biggest area is " + str(q.fetchone()[0])

        # if it is "-er" related questions
        elif JJR:
            # depth related questions
            if "deeper" in JJR:
                oceans = []
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP":
                        oceans.append(a)

                q1 = cur.execute("Select Deepest From Seas Where Ocean like \'%%%s%%\'" % oceans[0])
                first = q1.fetchone()
                q2 = cur.execute("Select Deepest From Seas Where Ocean like \'%%%s%%\'" % oceans[1])
                second = q2.fetchone()
                conn.close()
                if first > second:
                    return "Yes"
                else:
                    return "No"

            # height related questions
            elif "taller" in JJR or "higher" in JJR:
                mountains = []
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP":
                        mountains.append(a)

                q1 = cur.execute("Select Height From Mountains Where Name like \'%%%s%%\'" % mountains[0])
                first = q1.fetchone()
                q2 = cur.execute("Select Height From Mountains Where Name like \'%%%s%%\'" % mountains[1])
                second = q2.fetchone()
                conn.close()
                if first > second:
                    return "Yes"
                else:
                    return "No"

        # if is it capital related questions
        elif "capital" in NN:
            # yes or no questions
            if "Is" == bunch[0]:
                country = []
                for things in result:
                    (a, b) = things
                    if b == "LOCATION":
                        country.append(a)
                q = cur.execute("Select * From Capitals, Countries, Cities " +
                                "Where Cities.Name Like \'%%%s%%\' and Countries.Name Like \'%%%s%%\' and " %
                                (country[0], country[1]) +
                                "Capitals.CityId = Cities.Id and Capitals.CountryId = Countries.Id ")
                answer = q.fetchone()
                conn.close()

                if answer:
                    return "Yes"
                else:
                    return "No"

            # Wh- related questions
            else:
                country = []
                for things in result:
                    (a, b) = things
                    if b == "LOCATION":
                        country.append(a)
                q = cur.execute("Select Cities.Name From Capitals, Countries, Cities " +
                                "Where Countries.Name Like \'%%%s%%\' and " % country[0] +
                                "Capitals.CountryId = Countries.Id and Capitals.CityId = Cities.Id")
                answer = q.fetchone()
                conn.close()

                if answer:
                    return str(answer[0]) + " is the capital of " + str(country[0])
                else:
                    return "Answer not found!"

        # border related questions
        elif "border" in bunch:
            # yes or no questions
            if "Is" == bunch[0]:
                country = []
                for things in result:
                    (a, b) = things
                    if b == "LOCATION":
                        country.append(a)
                q1 = cur.execute("Select ID From Countries Where Name = \'%%%s%%\'" % country[0])
                q1 = q1.fetchone()
                q2 = cur.execute("Select ID From Countries Where Name = \'%%%s%%\'" % country[1])
                q2 = q2.fetchone()
                q = cur.execute("Select * From Borders Where Country1 = %s and Country2 = %s" % (q1, q2))
                answer = q.fetchone()

                if answer:
                    return "Yes"
                else:
                    q = cur.execute("Select * From Borders Where Country1 = %s and Country2 = %s" % (q2, q1))
                    answer = q.fetchone()
                    conn.close()

                    if answer:
                        return "Yes"
                    else:
                        return "No"

            # Wh- related questions
            else:
                country = []
                for things in result:
                    (a, b) = things
                    if b == "LOCATION":
                        country.append(a)

                tempList = []
                for row in cur.execute("Select Countries.Name From " +
                                       "(Select Borders.Country2 From Countries, Borders " +
                                       "Where Countries.Name like \'%%%s%%\' and " % country[0] +
                                       "Borders.Country1 = Countries.Id) as t1, Countries " +
                                       "Where t1.Country2 = Countries.Id"):
                    tempList.append(row[0])

                for row in cur.execute("Select Countries.Name From " +
                                       "(Select Borders.Country1 From Countries, Borders " +
                                       "Where Countries.Name like \'%%%s%%\' " % country[0] +
                                       "and Borders.Country2 = Countries.Id) as t1, Countries " +
                                       "Where t1.Country1 = Countries.Id"):
                    tempList.append(row[0])

                answer = ""
                if tempList:
                    answer += str(country[0]) + " is bordered with "
                    if len(tempList) > 2:
                        for things in range(len(tempList) - 1):
                            answer += str(tempList[things]) + ', '
                        answer += "and " + str(tempList[len(tempList) - 1])
                    elif len(tempList) == 2:
                        answer += str(tempList[0]) + " and " + str(tempList[1])
                    else:
                        answer += str(tempList[0])
                conn.close()
                return answer

        # continent related questions
        elif "continent" in bunch:
            country = []
            for things in result:
                (a, b) = things
                if b == "LOCATION":
                    country.append(a)
            q = cur.execute("Select Continents.Continent From Countries, CountryContinents, Continents "
                            "Where Countries.Name = \'%s\' " % country[0] +
                            "and Countries.Id = CountryContinents.CountryId " +
                            "and Continents.Id = CountryContinents.ContinentId")
            answer = q.fetchone()
            conn.close()

            if answer:
                return str(country[0]) + " is in " + str(answer[0])
            else:
                return "Answer not found!"

        # location comparison questions
        elif len(loc) >= 2:
            if bunch[0] == "Is" and "in" in bunch:
                country = []
                for things in result:
                    (a, b) = things
                    if b == "LOCATION":
                        country.append(a)
                q1 = cur.execute("Select ID From Countries Where Name Like \'%%%s%%\'" % country[0])
                q1 = q1.fetchone()[0]
                q2 = cur.execute("Select ID From Continents Where Continent Like \'%%%s%%\'" % country[1])
                q2 = q2.fetchone()[0]
                q = cur.execute("Select * From CountryContinents Where CountryId = %s and ContinentId = %s" % (q1, q2))
                answer = q.fetchone()

                if answer:
                    return "Yes"
                else:
                    q = cur.execute("Select * From Borders Where Country1 = %s and Country2 = %s" % (q2, q1))
                    answer = q.fetchone()
                    conn.close()

                    if answer:
                        return "Yes"
                    else:
                        return "No"

    # music related questions
    elif music:
        conn = sqlite3.connect("./DB/music.db")
        cur = conn.cursor()

        # who or what type of questions
        if "Who" in bunch or "Which" in bunch:
            # question about tracks
            if "sing" in bunch or "sings" in bunch or "song" in bunch or "track" in bunch:
                # find and parse out title of the song
                songs = []
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP" or b == "NNS":
                        songs.append(a)

                if len(songs) == 0:
                    for things in NN:
                        if things[0].isupper():
                            songs.append(thing)

                name = re.findall('[A-Z][a-z]*', songs[0])
                song = ""
                for things in range(0, len(name) - 1):
                    song = song + name[things] + " "
                song = song + name[len(name) - 1]

                q = cur.execute("Select Artist.name From Track, Artist Where " +
                                "Track.name Like \'%%%s%%\' and Track.trackID = Artist.Id" % song)
                answer = q.fetchone()
                conn.close()

                if answer:
                    return str(answer[0])
                else:
                    return "Answer not found!"

            # album related questions with related to artist
            elif ("album" in bunch and "artist" in bunch) or ("Who" in bunch and "album" in bunch):
                # parse out the title of album
                album = []
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP" or b == "NNS":
                        album.append(a)
                if len(album) == 0:
                    for things in NN:
                        if things[0].isupper():
                            album.append(things)

                name = re.findall('[A-Z][a-z]*', album[0])
                song = ""
                for things in range(0, len(name) - 1):
                    song = song + name[things] + " "
                song = song + name[len(name) - 1]

                q = cur.execute("Select Artist.name From Album, Artist Where " +
                                "Album.name Like \'%%%s%%\' and Album.artsitID = Artist.Id" % song)
                answer = q.fetchone()
                conn.close()

                if answer:
                    return str(answer[0])
                else:
                    return "Answer not found!"

            # album related questions
            elif "album" in bunch and ("Which" in bunch or "which" in bunch):
                artist = []
                songs = []
                for things in result:
                    (a, b) = things
                    if b == "PERSON":
                        artist.append(a)
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP" or b == "NNS":
                        songs.append(a)
                if len(songs) == 0:
                    for things in NN:
                        if things[0].isupper():
                            songs.append(thing)

                # artist specific questions
                if artist:
                    if CD:
                        q = cur.execute("Select Album.name From Album, Artist " +
                                        "Where Artist.name Like \'%%%s%%\' " % artist[0] +
                                        "and Artist.id = Album.artsitID and Album.releaseDate Like \'%%%s%%\'" % CD[0])
                        return "Album name is " + str(q.fetchone()[0])
                    else:
                        answer = []
                        astr = ""
                        for row in cur.execute("Select Album.name From Album, Artist " +
                                               "Where Artist.name Like \'%%%s%%\' " % artist[0] +
                                               "and Artist.id = Album.artsitID"):
                            answer.append(row[0])
                            astr += str(artist[0]) + " made: "
                        conn.close()
                        for things in range(0, len(answer) - 1):
                            astr += str(answer[things]) + ", "
                        astr += str(answer[len(answer) - 1])
                        return astr

                # track specific questions
                elif songs:
                    name = re.findall('[A-Z][a-z]*', songs[0])
                    song = ""
                    for things in range(0, len(name) - 1):
                        song = song + name[things] + " "
                    song = song + name[len(name) - 1]

                    q = cur.execute("Select Album.name From Album, Track Where Track.name Like \'%%%s%%\' " % song +
                                    "and Track.albumID = Album.albumID")
                    answer = q.fetchone()
                    conn.close()

                    if answer:
                        return "Album name is " + str(q.fetchone()[0])
                    else:
                        return "Answer not found!"

        # yes or no questions
        elif "Did" in bunch or "Is" in bunch:
            artist = []
            songs = []
            for things in result:
                (a, b) = things
                if b == "PERSON":
                    artist.append(a)
            for things in thing.pos():
                (a, b) = things
                if b == "NNP" or b == "NNS":
                    songs.append(a)
            if len(songs) == 0:
                for things in NN:
                    if things[0].isupper():
                        songs.append(thing)
            songs.remove(artist[0])

            if artist and songs:
                name = re.findall('[A-Z][a-z]*', songs[0])
                song = ""
                for things in range(0, len(name) - 1):
                    song = song + name[things] + " "
                song = song + name[len(name) - 1]
                q = cur.execute("Select * From Track, Artist, Album Where Track.albumID = Album.albumID " +
                                "and Album.artsitID = Artist.id and Artist.name Like \'%%%s%%\'" % artist[0] +
                                "and Track.name Like \'%%%s%%\' " % song)
                answer = q.fetchone()
                conn.close()

                if answer:
                    return "Yes"
                else:
                    return "No"

    # movie related questions
    elif movie:
        conn = sqlite3.connect("./DB/oscar-movie_imdb.db")
        cur = conn.cursor()

        # best picture related questions
        if "best movie" in question or "best film" in question or "best picture" in question:
            # find if any person is mentions in the question
            persons = []
            for things in result:
                (a, b) = things
                if b == "PERSON":
                    persons.append(a)

            # if there is more than 1 person mentioned
            if len(persons) == 2:
                if "Which" in bunch or "What" in bunch:
                    q1 = cur.execute("Select t1.name From "
                                     "(Select Movie.name From Person, Oscar, Movie, Actor " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Actor.actor_id " % persons[0] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Actor.movie_id = Movie.id) as t1, "
                                     "(Select Movie.name From Person, Oscar, Movie, Director " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                     persons[1] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Director.movie_id = Movie.id) as t2 Where t1.name = t2.name ")
                    q2 = cur.execute("Select t1.name From "
                                     "(Select Movie.name From Person, Oscar, Movie, Actor " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Actor.actor_id " % persons[1] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Actor.movie_id = Movie.id) as t1, "
                                     "(Select Movie.name From Person, Oscar, Movie, Director " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                     persons[0] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Director.movie_id = Movie.id) as t2 Where t1.name = t2.name ")
                    a1 = q1.fetchone()
                    a2 = q2.fetchone()
                    conn.close()

                    if a1:
                        return str(a1[0])
                    elif a2:
                        return str(a2[0])
                    else:
                        return "Answer not found!"

                # yes or no questions
                elif "Did" in bunch:
                    q1 = cur.execute("Select t1.name From "
                                     "(Select Movie.name From Person, Oscar, Movie, Actor " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Actor.actor_id " % persons[0] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Actor.movie_id = Movie.id) as t1, "
                                     "(Select Movie.name From Person, Oscar, Movie, Director " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                     persons[1] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Director.movie_id = Movie.id) as t2 Where t1.name = t2.name ")
                    q2 = cur.execute("Select t1.name From "
                                     "(Select Movie.name From Person, Oscar, Movie, Actor " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Actor.actor_id " % persons[1] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Actor.movie_id = Movie.id) as t1, "
                                     "(Select Movie.name From Person, Oscar, Movie, Director " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                     persons[0] +
                                     "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                     "and Director.movie_id = Movie.id) as t2 Where t1.name = t2.name ")
                    a1 = q1.fetchone()
                    a2 = q2.fetchone()
                    conn.close()

                    if a1:
                        return "Yes"
                    elif a2:
                        return "Yes"
                    else:
                        return "No"

            # if only 1 person is mentioned
            elif len(persons) == 1:
                # yes or no question
                if "Did" in bunch or "Is" in bunch:
                    # is actor specific questions
                    if "star" in bunch or "in" in bunch:
                        q = cur.execute("Select * From Person, Oscar, Movie, Actor " +
                                        "Where Person.name like \'%%%s%%\' and Person.id = Actor.id " % persons[0] +
                                        "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                        "and Actor.movie_id = Movie.id ")
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return "Yes"
                        else:
                            return "No"

                    # if director specific questions
                    elif "by" in bunch or "direct" in bunch or "directed" in bunch:
                        q = cur.execute("Select * From Person, Oscar, Movie, Director " +
                                        "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                        persons[0] +
                                        "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                        "and Director.movie_id = Movie.id ")
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return "Yes"
                        else:
                            return "No"

                # Wh- type of questions
                else:
                    # actor specific questions
                    if "star" in bunch or "in" in bunch or "starred" in bunch:
                        q = cur.execute("Select Movie.name From Person, Oscar, Movie, Actor " +
                                        "Where Person.name like \'%%%s%%\' and Person.id = Actor.id " % persons[0] +
                                        "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                        "and Actor.movie_id = Movie.id ")
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return str(persons[0]) + " starred in movie " + str(answer[0])
                        else:
                            return "Answer not found!"

                    # director specific questions
                    elif "by" in bunch or "direct" in bunch or "directed" in bunch:
                        if CD:
                            q = cur.execute("Select Movie.name From Person, Oscar, Movie, Director " +
                                            "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                            persons[0] +
                                            "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                            "and Director.movie_id = Movie.id and Oscar.year = %s " % CD[0])
                            answer = q.fetchone()
                            conn.close()

                            if answer:
                                return str(answer[0])
                            else:
                                return "Answer not found!"

                        else:
                            q = cur.execute("Select Movie.name From Person, Oscar, Movie, Director " +
                                            "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                            persons[0] +
                                            "and Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                            "and Director.movie_id = Movie.id ")
                            answer = q.fetchone()
                            conn.close()

                            if answer:
                                return str(answer[0])
                            else:
                                return "Answer not found!"

            # if no person is mentioned
            elif len(persons) == 0:
                # director specific questions
                if "directed" in bunch:
                    if CD:
                        q = cur.execute("Select Person.name From Person, Director, Oscar " +
                                        "Where Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Director.movie_id " +
                                        "and Director.director_id = Person.id and Oscar.year = %s" % CD[0])
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return str(answer[0]) + " directed the best-picture in " + str(CD[0])
                        else:
                            return "Answer not found!"

                # other tpe of questions
                else:
                    q = cur.execute("Select Movie.name From Movie, Oscar " +
                                    "Where Oscar.type = \'BEST-PICTURE\' and Oscar.movie_id = Movie.id " +
                                    "and Oscar.year = %s" % CD[0])
                    answer = q.fetchone()
                    conn.close()

                    if answer:
                        return str(answer[0]) + " won the best-picture in " + str(CD[0])
                    else:
                        return "Answer not found!"

        # other type of best oscar questions
        elif "best" in bunch:
            # find if it is best (supporting) actor or actress
            tempstr1 = ""
            tempstr2 = ""
            if "actor" in question:
                tempstr1 = "BEST-ACTOR"
                tempstr2 = "best actor"
            elif "actress" in question:
                tempstr1 = "BEST-ACTRESS"
                tempstr2 = "best actress"
            elif "supporting actor" in question or "supporting-actor" in question:
                tempstr1 = "BEST-SUPPORTING-ACTOR"
                tempstr2 = "best supporting actor"
            elif "supporting actress" in question or "supporting-actress" in question:
                tempstr1 = "BEST-SUPPORTING-ACTRESS"
                tempstr2 = "best supporting actress"
            elif "director" in bunch or "best director" in question:
                tempstr1 = "BEST-DIRECTOR"
                tempstr2 = "best director"

            persons = []
            for things in result:
                (a, b) = things
                if b == "PERSON":
                    persons.append(a)

            # if person if mentioned
            if len(persons) == 1:
                # date related questions
                if "When" in bunch:
                    q = cur.execute("Select Oscar.year From Oscar, Person Where Oscar.type = \'%s\' " % tempstr1 +
                                    "and Oscar.person_id = Person.id and Person.name Like \'%%%s%%\' " % persons[0])
                    answer = q.fetchone()
                    conn.close()

                    if answer:
                        return str(persons[0]) + " won " + str(tempstr2) + " in " + str(answer[0])
                    else:
                        return "Answer not found!"

                # movie title related questions
                elif "What" in bunch or "Which" in bunch:
                    q = cur.execute(
                        "Select Movie.name From Oscar, Person, Movie Where Oscar.type = \'%s\' " % tempstr1 +
                        "and Oscar.person_id = Person.id and Person.name Like \'%%%s%%\' " % persons[0] +
                        "and Movie.id = Oscar.movie_id")
                    answer = q.fetchone()
                    conn.close()

                    if answer:
                        return str(persons[0]) + " won " + str(tempstr2) + " in movie " + str(answer[0])
                    else:
                        return "Answer not found!"

                # yes or no questions
                elif "Did" in bunch:
                    if CD:
                        q = cur.execute("Select * From Oscar, Person Where Oscar.type = \'%s\' " % tempstr1 +
                                        "and Oscar.person_id = Person.id and Person.name Like \'%%%s%%\' " % persons[
                                            0] +
                                        "and Oscar.year = %s" % CD[0])
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return "Yes"
                        else:
                            return "No"

                    else:
                        q = cur.execute("Select * From Oscar, Person Where Oscar.type = \'%s\' " % tempstr1 +
                                        "and Oscar.person_id = Person.id and Person.name Like \'%%%s%%\' " % persons[0])
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return "Yes"
                        else:
                            return "No"

            # if no person is mentioned
            elif len(persons) == 0:
                if "Who" in bunch:
                    if CD:
                        q = cur.execute("Select Person.name From Person, Oscar Where Oscar.type = \'%s\' " % tempstr1 +
                                        "and Oscar.person_id = Person.id and Oscar.year = %s" % CD[0])
                        answer = q.fetchone()
                        conn.close()

                        if answer:
                            return str(answer[0]) + " won " + str(tempstr2) + " in " + str(CD[0])
                        else:
                            return "Answer not found!"

        # director specific questions
        elif "directed" in bunch:
            # person related questions
            if "Who" in bunch:
                movie_name = []
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP" or b == "NNS":
                        movie_name.append(a)

                if len(movie_name) == 0:
                    for things in NN:
                        if things[0].isupper():
                            movie_name.append(thing)

                name = re.findall('[A-Z][a-z]*', movie_name[0])
                title = ""
                for things in range(0, len(name) - 1):
                    title = title + name[things] + " "
                title = title + name[len(name) - 1]
                q = cur.execute("Select Person.name From Person, Director, Movie " +
                                "Where Movie.name Like \'%%%s%%\' and Movie.id = Director.movie_id " % title +
                                "and Person.id = Director.director_id")
                answer = q.fetchone()
                conn.close()

                if answer:
                    return str(answer[0]) + " directed movie " + str(title)
                else:
                    return "Answer not found!"

            # yes or no questions
            if "Did" in bunch:
                movie_name = []
                for things in thing.pos():
                    (a, b) = things
                    if b == "NNP" or b == "NNS":
                        movie_name.append(a)

                if len(movie_name) == 0:
                    for things in NN:
                        if things[0].isupper():
                            movie_name.append(thing)

                name = re.findall('[A-Z][a-z]*', movie_name[0])
                title = ""
                for things in range(0, len(name) - 1):
                    title = title + name[things] + " "
                title = title + name[len(name) - 1]

                director = []
                for things in result:
                    (a, b) = things
                    if b == "PERSON":
                        director.append(a)
                NNP.remove(director[0])

                q = cur.execute("Select Person.name From Person, Director, Movie " +
                                "Where Movie.name Like \'%%%s%%\' and Movie.id = Director.movie_id " % title +
                                "and Person.id = Director.director_id and Person.name Like \'%%%s%%\' " % director[0])
                answer = q.fetchone()
                conn.close()

                if answer:
                    return "Yes"
                else:
                    return "No"

        # actor/actress specific questions
        elif "starred" in bunch or "star" in bunch:
            movie_name = []
            for things in thing.pos():
                (a, b) = things
                if b == "NNP" or b == "NNS":
                    movie_name.append(a)

            if len(movie_name) == 0:
                for things in NN:
                    if things[0].isupper():
                        movie_name.append(thing)

            name = re.findall('[A-Z][a-z]*', movie_name[0])
            title = ""
            for things in range(0, len(name) - 1):
                title = title + name[things] + " "
            title = title + name[len(name) - 1]

            if "Who" in bunch:
                people = []
                for things in cur.execute("Select Person.name From Person, Actor, Movie " +
                                          "Where Movie.name Like \'%%%s%%\' and Movie.id = Actor.movie_id " % title +
                                          "and Person.id = Actor.actor_id"):
                    people.append(things)
                conn.close()

                ans = ""
                if people:
                    for things in people:
                        ans += str(things[0]) + ", "
                    ans += ("starred in movie " + str(title))
                    return ans
                else:
                    return "Answer not found!"

            # yes or no questions
            if "Did" in bunch:
                director = []
                for things in result:
                    (a, b) = things
                    if b == "PERSON":
                        director.append(a)
                NNP.remove(director[0])

                q = cur.execute("Select Person.name From Person, Director, Movie " +
                                "Where Movie.name Like \'%%%s%%\' and Movie.id = Director.movie_id " % title +
                                "and Person.id = Director.director_id and Person.name Like \'%%%s%%\' " % director[0])
                answer = q.fetchone()
                conn.close()

                if answer:
                    return "Yes"
                else:
                    return "No"

        # other oscar related questions
        elif "oscar" in bunch:
            # find if it is actor or actress or director related questions
            tempstr1 = ""
            tempstr3 = ""
            if "actor" in question:
                tempstr1 = "BEST-ACTOR"
                tempstr3 = "BEST-SUPPORTING-ACTOR"
            elif "actress" in question:
                tempstr1 = "BEST-ACTRESS"
                tempstr3 = "BEST-SUPPORTING-ACTRESS"
            elif "director" in question:
                tempstr1 = "BEST-DIRECTOR"

            # if director related questions
            if "director" in bunch:
                q = cur.execute("Select Person.name From Oscar, Person Where " +
                                "Oscar.type Like \'%%%s%%\' and Oscar.person_id = Person.id " % tempstr1 +
                                "and Oscar.year = %s Group by Person.name" % CD[0])
            # other actor/actress related questions
            else:
                q = cur.execute("Select Person.name From Oscar, Person Where " +
                                "(Oscar.type Like \'%%%s%%\' or Oscar.type Like \'%%%s%%\') " % (tempstr1, tempstr3) +
                                "and Oscar.person_id = Person.id and Oscar.year = %s Group by Person.name" % CD[0])
            answer = q.fetchall()
            conn.close()

            if len(answer) == 1:
                return str(answer[0][0])
            else:
                return str(answer[0][0]) + " and " + str(answer[1][0])

        # other type of questions
        else:
            index = bunch.index("movie")
            index = index - 1
            type = genre(bunch[index])

            # genre specific questions
            if type:
                persons = []
                for things in result:
                    (a, b) = things
                    if b == "PERSON":
                        persons.append(a)

                # if two persons are mentioned
                if len(persons) == 2:
                    q1 = cur.execute("Select t1.name From "
                                     "(Select Movie.name From Person, Oscar, Movie, Actor " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Actor.actor_id " % persons[0] +
                                     "and Actor.movie_id = Movie.id and Movie.genre Like \'%%%s%%\') as t1, " % type +
                                     "(Select Movie.name From Person, Oscar, Movie, Director " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                     persons[1] +
                                     "and Director.movie_id = Movie.id and Movie.genre Like \'%%%s%%\') " % type +
                                     "as t2 Where t1.name = t2.name Group by t1.name")
                    q2 = cur.execute("Select t1.name From "
                                     "(Select Movie.name From Person, Oscar, Movie, Actor " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Actor.actor_id " % persons[1] +
                                     "and Actor.movie_id = Movie.id and Movie.genre Like \'%%%s%%\') as t1, " % type +
                                     "(Select Movie.name From Person, Oscar, Movie, Director " +
                                     "Where Person.name like \'%%%s%%\' and Person.id = Director.director_id " %
                                     persons[0] +
                                     "and Director.movie_id = Movie.id and Movie.genre Like \'%%%s%%\') " % type +
                                     "as t2 Where t1.name = t2.name Group by t1.name")

                    first = q1.fetchone()
                    second = q2.fetchone()
                    conn.close()

                    if first:
                        return str(first[0])
                    elif second:
                        return str(second[0])
                    else:
                        return "Answer not found"

                # if only 1 person is mentioned
                elif len(persons) == 1:
                    movie_name = []
                    for things in thing.pos():
                        (a, b) = things
                        if b == "NNP" or b == "NNS":
                            movie_name.append(a)

                    if len(movie_name) == 0:
                        for things in NN:
                            if things[0].isupper():
                                movie_name.append(thing)

                    name = re.findall('[A-Z][a-z]*', movie_name[0])
                    title = ""
                    for things in range(0, len(name) - 1):
                        title = title + name[things] + " "
                    title = title + name[len(name) - 1]

                    if "Who" in bunch or "Which" in bunch or "What" in bunch:
                        if "direct" in bunch or "directed" in bunch:
                            q = cur.execute("Select Person.name From Person, Movie, Director" +
                                            "Where Movie.name Like \'%%%s%%\' and " % title +
                                            "Movie.id = Director.movie_id " +
                                            "and Director.director_id = Person.id " +
                                            "and Movie.genre Like \'%%%s%%\'" % type)
                            answer = q.fetchone()
                            conn.close()

                            if answer:
                                return str(answer[0])
                            else:
                                return "Answer not found!"

                        elif "starred" in bunch or "star" in bunch or "in":
                            q = cur.execute("Select Person.name From Person, Movie, Actor" +
                                            "Where Movie.name Like \'%%%s%%\' and Movie.id = Actor.movie_id " % title +
                                            "and Actor.actor_id = Person.id and Movie.genre Like \'%%%s%%\'" % type)
                            answer = q.fetchone()
                            conn.close()

                            if answer:
                                return str(answer[0])
                            else:
                                return "Answer not found!"

    # no category is found
    else:
        return "Answer not found!"
