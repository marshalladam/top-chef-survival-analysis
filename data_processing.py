import pandas as pd
import numpy as np


###
# This function takes a raw demographic data frame and processes it
###
def processRawDemo(rawDemo, season, startID):
    #split Name column into first name and last name
    rawDemo["FirstName"], rawDemo["LastName"] = rawDemo["Name"].str.split(
        " ", 1).str
    #split Current Residence column into city and state
    rawDemo["ResidenceCity"], rawDemo["ResidenceState"] = rawDemo[
        "Current Residence"].str.split(", ").str
    #add a column for the season
    rawDemo["Season"] = season
    #drop the Name and Current Residence columns
    rawDemo = rawDemo.drop(["Name", "Current Residence"], axis=1)
    rawDemo = rawDemo[[
        "Season", "FirstName", "LastName", "Age", "ResidenceCity",
        "ResidenceState"
    ]]
    rawDemo.insert(0, 'ID', range(startID, startID+ rawDemo.shape[0]))
    return rawDemo

###
# This function takes a raw elimination challenge data and converts it to a table
# where each row is a contestant and the columns are:
# Quickfire Wins
# Wins
# Highs
# Lows
# Winner
###
def processRawElimination(raw_elim, sharedWins):
    ###first we deal with the quickfire wins####
    #quickfire winners are in the first row of the table.
    quickfirewinners = raw_elim.iloc[[0]].values.tolist()[0]
    #remove the first element, since this is just the word "Quickfire"
    del quickfirewinners[0]
    #remove any element that is "", since this indicates an episode with no quickfire
    quickfirewinners = [val for val in quickfirewinners if val != '']

    #There are shared quickfire wins and we have to process the values accordingly
    qfwins = {}
    for i in range(0, len(quickfirewinners)):
        winners = quickfirewinners[i]
        winners = winners.split(",")
        if not sharedWins:
            winneradd = 1
        else:
            #we want to share the wins, which means if two people won the quickfire,
            #it gets counted as 1/2 of a win for each person
            winneradd = 1 / len(winners)
        for name in winners:
            #add to a dictionary where the keys are the names and the value is the number of wins
            qfwins[name] = qfwins.get(name, 0) + winneradd
    #convert to dataframe
    qfwinners = pd.DataFrame(
        list(qfwins.items()), columns=["Name", "QuickfireWins"])

    #now we deal with the rest of the raw_elim table, which deals with the elimination results
    processed_elim = []
    for i in range(1, raw_elim.shape[0]):
        #each row is one contestants progress, so we iterate through each row and count the nubmer of wins, highs, lows, and winner (if they won the season)
        row = raw_elim.iloc[[i]].values.tolist()[0]
        name = row[0]
        wins = 0
        highs = 0
        lows = 0
        winner = 0
        for j in range(1, len(row)):
            if (row[j] == "WIN"):
                wins += 1
            elif (row[j] == "LOW"):
                lows += 1
            elif (row[j] == "HIGH"):
                highs += 1
            elif (row[j] == "WINNER"):
                winner += 1
        processed_elim.append([name, wins, highs, lows, winner])

    if (sharedWins):
        #now we look at each column to see if there are shared wins
        for i in range(1, raw_elim.shape[1]):
            episode = raw_elim.iloc[1:, [0, i]]
            episode.columns = ["Name", "Result"]
            episodewinners = episode.loc[episode["Result"] == "WIN"]
            episodewinnersnames = episodewinners["Name"].values.tolist()
            #print(episodewinners)
            if episodewinners.shape[0] > 1:
                #get the number of winners and calculate the shared win value
                #
                numwinners = episodewinners.shape[0]
                winaddval = 1 / numwinners
                #iterate through each element of processed_elim, if the first element
                #(the name) is in the episodewinners array, we adjust their win count accordingly
                for val in processed_elim:
                    if val[0] in episodewinnersnames:
                        val[1] = val[1] - 1 + winaddval

    #convert processed elim into a dataframe
    processed_elim = pd.DataFrame(
        processed_elim, columns=["Name", "Wins", "Highs", "Lows", "Winner"])
    processed_elim = pd.merge(qfwinners, processed_elim, how='outer')
    processed_elim = processed_elim.fillna(0)
    return processed_elim

###
# This function takes a raw elimination challenge data and converts it to a table
# where each row is a contestant's results per episode and the columns are:
# Start 
# End (The Start/End columns are needed for the survival analysis.)
# Quickfire Wins
# Wins
# Highs
# Lows
# Out
###
def processRawEliminationByEpisode(raw_elim, sharedWins):
    contestants = raw_elim.iloc[1:, 0].values.tolist()
    ###first we deal with the quickfire wins####
    #quickfire winners are in the first row of the table.
    quickfirewinners = raw_elim.iloc[[0]].values.tolist()[0]
    #remove the first element, since this is just the word "Quickfire"
    del quickfirewinners[0]
    #now we deal with the rest of the raw_elim table, which deals with the elimination results
    eliminationResultsByEpisode = []
    for i in range(1, raw_elim.shape[1]):
        episodeData = pd.DataFrame(
            0,
            index=np.arange(len(contestants)),
            columns=["Start", "End","Wins", "Highs", "Lows", "QuickfireWins", "Out"])
        episodeData["Name"] = contestants
        quickfireWinnerOfEpisode = quickfirewinners[i - 1]
        quickfireWinnerOfEpisode = quickfireWinnerOfEpisode.split(",")
        if (quickfireWinnerOfEpisode != ""):
            if not sharedWins:
                winneradd = 1
            else:
                winneradd = 1 / len(quickfireWinnerOfEpisode)
        episodeData.loc[episodeData["Name"].isin(quickfireWinnerOfEpisode),
                        "QuickfireWins"] += winneradd
        eliminationResults = raw_elim.iloc[1:, [0, i]]
        eliminationResults.columns = ["Name", "Result"]
        eliminatedContestants = eliminationResults.loc[
            eliminationResults["Result"] == ""]
        #remove anyone who was eliminated
        episodeData = episodeData.loc[~episodeData["Name"].
                                        isin(eliminatedContestants["Name"])]
        eliminationResults = eliminationResults.loc[
            ~eliminationResults["Name"].isin(eliminatedContestants["Name"])]

        numWinners = eliminationResults.loc[eliminationResults["Result"] ==
                                            "WIN"].shape[0]
        if (not sharedWins or numWinners == 0):
            eliminationWinnerAdd = 1
        else:
            eliminationWinnerAdd = 1 / numWinners
        for j in range(eliminationResults.shape[0]):
            c = eliminationResults.iloc[j]
            if c.Result == "WIN":
                episodeData.loc[episodeData["Name"] == c.
                                Name, "Wins"] += eliminationWinnerAdd
            elif c.Result == "LOW":
                episodeData.loc[episodeData["Name"] == c.Name, "Lows"] += 1
            elif c.Result == "HIGH":
                episodeData.loc[episodeData["Name"] == c.
                                Name, "Highs"] += eliminationWinnerAdd
            elif c.Result == "OUT" or c.Result == "WD":
                episodeData.loc[episodeData["Name"] == c.
                                Name, "Out"] += 1
        #add last episodes results to this episode's
        if (i > 1):
            lastEpisode = eliminationResultsByEpisode[i - 2]
            lastEpisode = lastEpisode.loc[lastEpisode["Name"].isin(
                episodeData["Name"])]
            episodeDataSum = lastEpisode.iloc[:, 0:6] + episodeData.iloc[:, 0:6]
            episodeDataSum["Name"] = lastEpisode["Name"]
            episodeDataSum["Out"] = episodeData["Out"]
        else:
            episodeDataSum = episodeData
        #We need these columns for the survival analysis
        episodeDataSum["Start"] = i - 1
        episodeDataSum["End"] = i
        #For subsetting later
        episodeDataSum["Episode"] = i + 1
        #episodeDataSum["Place"] = episodeData.index + 1
        #Number of people in competition left. 
        episodeDataSum["CompLeft"] = episodeData.shape[0] 
        eliminationResultsByEpisode.append(episodeDataSum)
    return eliminationResultsByEpisode


def processData(rawDemoFileName, rawElimFileName, season, sharedWins, startID):
    #read in raw data
    rawDemo = pd.read_csv(rawDemoFileName)
    rawElim = pd.read_csv(rawElimFileName, header=None, na_filter=False)
    #process data using helper functions
    processedDemo = processRawDemo(rawDemo, season, startID)
    processedElim = processRawElimination(rawElim, sharedWins)
    #merge our two tables
    combinedData = pd.merge(
        processedDemo,
        processedElim,
        how='left',
        left_on=['FirstName'],
        right_on=['Name'])
    combinedData = combinedData.drop(["Name"], axis=1)
    #sort so that the winner is on top, and then sorted by number of wins
    combinedData = combinedData.sort_values(["Winner", "Wins"],
                                            ascending=[False, False])
    return combinedData


def processDataByEpisode(rawDemoFileName, rawElimFileName, season, sharedWins, startID):
    #read in raw data
    rawDemo = pd.read_csv(rawDemoFileName)
    rawElim = pd.read_csv(rawElimFileName, header=None, na_filter=False)
    #process data using helper functions
    processedDemo = processRawDemo(rawDemo, season, startID)
    processedElimByEpisode = processRawEliminationByEpisode(
        rawElim, sharedWins)
    combinedDataByEpisode = []
    for i in range(len(processedElimByEpisode)):
        processedElimSub = processedElimByEpisode[i]
        combinedData = pd.merge(
            processedDemo,
            processedElimSub,
            how='inner',
            left_on=['FirstName'],
            right_on=['Name'])
        combinedData = combinedData.drop(["Name"], axis=1)
        #sort so that the winner is on top, and then sorted by number of wins
        combinedData = combinedData.sort_values(["Wins"], ascending=[False])
        combinedData = combinedData[["ID",
            "Season", "FirstName", "LastName", "Age", "ResidenceCity",
            "ResidenceState", "CompLeft", "Start", "End", "Episode", "QuickfireWins", "Wins", "Highs", "Lows", "Out"
        ]]
        combinedDataByEpisode.append(combinedData)
    return combinedDataByEpisode


def loadSeasonData(season, sharedWins, startID):
    seasonstring = str(season)
    rawDemoFileName = "./data/Season " + seasonstring + "/s" + seasonstring + "_raw_demo.csv"
    rawElimFileName = "./data/Season " + seasonstring + "/s" + seasonstring + "_raw_elimination.csv"
    seasonData = processData(rawDemoFileName, rawElimFileName, season,
                             sharedWins, startID)
    return seasonData


def loadSeasonDataByEpisode(season, sharedWins, startID):
    seasonstring = str(season)
    rawDemoFileName = "./data/Season " + seasonstring + "/s" + seasonstring + "_raw_demo.csv"
    rawElimFileName = "./data/Season " + seasonstring + "/s" + seasonstring + "_raw_elimination.csv"
    seasonData = processDataByEpisode(rawDemoFileName, rawElimFileName, season,
                                      sharedWins, startID)
    return seasonData

###
# Loads all available seasons contestant data by episode.
###
def loadAllTrainData(sharedWins):
    allSeasons = []
    possibleSeasons = [1,2,3,4,5,6,7,9,10,11,12,13]
    startID = 1
    for season in possibleSeasons:
        seasonData = loadSeasonDataByEpisode(season, sharedWins, startID)
        seasonData = pd.concat(seasonData)
        startID = 1 + max(seasonData["ID"])
        allSeasons.append(seasonData)
    return pd.concat(allSeasons)

###
# Loads all available seasons contestant data. This is a summary, not by episode.
###
def loadAllData(sharedWins):
    allSeasons = []
    possibleSeasons = [1,2,3,4,5,6,7,9,10,11,12,13]
    startID = 1
    for season in possibleSeasons:
        seasonData = loadSeasonData(season, sharedWins, startID)
        startID = 1 + max(seasonData["ID"])
        allSeasons.append(seasonData)
    return pd.concat(allSeasons)

