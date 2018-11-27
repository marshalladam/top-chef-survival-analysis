import data_processing
import matplotlib.pyplot as plt
import pandas as pd

"""
Load Data
"""
#load summary data of all seasons
allSeasons = data_processing.loadAllData(True)
#load all training data (each row is a contestant at an episode)
allSeasonsByEpisode = data_processing.loadAllTrainData(False)
allSeasonsByEpisode = allSeasonsByEpisode.sort_values(["ID", "Season", "Episode"],
                                            ascending=[True, True, True])


"""
Some pre-processing – namely, there are three contestants whose age was missing on Wikipedia.
We are going to fill it in for the average age of the other contestants
"""
averageAge = allSeasons[allSeasons["Age"] != 0]["Age"].mean()
allSeasons.loc[allSeasons.Age == 0, "Age"] = averageAge

"""
Do some basic analysis about the winners.
"""
#Some basic analysis about the winners
allSeasonsWinners = allSeasons.loc[allSeasons["Winner"] == 1]

#Averages of winners
allSeasonsWinnersAverages = allSeasonsWinners[[
    "Age", "QuickfireWins", "Wins", "Highs", "Lows"
]].mean()
print("Winner Averages:")
print("Average Age: " + '{0:.3g}'.format(allSeasonsWinnersAverages.Age))
print("Average QuickfireWins: " +
      '{0:.3g}'.format(allSeasonsWinnersAverages.QuickfireWins))
print("Average Wins: " + '{0:.3g}'.format(allSeasonsWinnersAverages.Wins))
print("Average Highs: " + '{0:.3g}'.format(allSeasonsWinnersAverages.Highs))
print("Average Lows: " + '{0:.3g}'.format(allSeasonsWinnersAverages.Lows))

#Averages of non-winners
allSeasonsNotWinners = allSeasons.loc[allSeasons["Winner"] != 1]
allSeasonsNotWinnersAverages = allSeasonsNotWinners[[
    "Age", "QuickfireWins", "Wins", "Highs", "Lows"
]].mean()
print("Non-Winner Averages:")
print("Average Age: " + '{0:.3g}'.format(allSeasonsNotWinnersAverages.Age))
print("Average QuickfireWins: " +
      '{0:.3g}'.format(allSeasonsNotWinnersAverages.QuickfireWins))
print("Average Wins: " + '{0:.3g}'.format(allSeasonsNotWinnersAverages.Wins))
print("Average Highs: " + '{0:.3g}'.format(allSeasonsNotWinnersAverages.Highs))
print("Average Lows: " + '{0:.3g}'.format(allSeasonsNotWinnersAverages.Lows))

#Plot pie chart of states of residence of winners
allSeasonsWinnersState = allSeasonsWinners["ResidenceState"]
allSeasonsWinnersState = allSeasonsWinnersState.values.tolist()
total = len(allSeasonsWinnersState)
winnersStateCounts = {}
for state in allSeasonsWinnersState:
    winnersStateCounts[state] = winnersStateCounts.get(state, 0) + 1
allSeasonsWinnersStateLabels = [x for x, v in winnersStateCounts.items()]
allSeasonsWinnersStateSizes = [v for x, v in winnersStateCounts.items()]

fig1, ax1 = plt.subplots()
ax1.pie(
    allSeasonsWinnersStateSizes,
    labels=allSeasonsWinnersStateLabels,
    autopct='%1.1f%%',
    shadow=True,
    startangle=90)
ax1.axis('equal')
plt.show()


"""
Survival Analysis
"""
#Subset the training data
from lifelines import KaplanMeierFitter
####EDIT THIS TO CHANGE WHICH SEASON YOU TRAIN THE MODEL ON#####
trainingSeasons = [1,2,3,4,5,6,7,9,10,11,12]

trainData = allSeasonsByEpisode.loc[allSeasonsByEpisode["Season"].isin(trainingSeasons)]

kmfdata = pd.DataFrame({'Age':allSeasonsByEpisode.groupby(['ID']).Age.first(), 'Duration':allSeasonsByEpisode.groupby(['ID']).End.max(), 'Observed':allSeasonsByEpisode.groupby(['ID']).Out.sum() == 1})

kmf = KaplanMeierFitter()
kmf.fit(kmfdata["Duration"], event_observed=kmfdata["Observed"])

#Segment the surival curve based on age group
ax = plt.subplot(111)
age0 = kmfdata["Age"] < 30
age1 = (kmfdata["Age"] < 40) & (kmfdata["Age"] >= 30)
age2 = kmfdata["Age"] >= 40
kmf.fit(kmfdata["Duration"][age0], event_observed=kmfdata["Observed"][age0], label="Age < 30")
kmf.plot(ax=ax)
kmf.fit(kmfdata["Duration"][age1], event_observed=kmfdata["Observed"][age1], label=" 30 <= Age < 40")
kmf.plot(ax=ax)
kmf.fit(kmfdata["Duration"][age2], event_observed=kmfdata["Observed"][age2], label=" Age >= 40")
kmf.plot(ax=ax)
plt.ylim(0, 1)
plt.title("Survival separated by age group")
plt.show()

#Segment the surival curve based on number of wins
ax = plt.subplot(111)
kmfdata["Wins"] = allSeasonsByEpisode.groupby(['ID']).Wins.max() 
wins0 = kmfdata["Wins"] < 1
wins1 = (kmfdata["Wins"] < 2) & (kmfdata["Wins"] >= 1)
wins2 = (kmfdata["Wins"] < 3) & (kmfdata["Wins"] >= 2) 
wins3 =  (kmfdata["Wins"] >= 3) 
kmf.fit(kmfdata["Duration"][wins0], event_observed=kmfdata["Observed"][wins0], label="0 - 1")
kmf.plot(ax=ax)
kmf.fit(kmfdata["Duration"][wins1], event_observed=kmfdata["Observed"][wins1], label="1 - 2")
kmf.plot(ax=ax)
kmf.fit(kmfdata["Duration"][wins2], event_observed=kmfdata["Observed"][wins2], label="2 - 3")
kmf.plot(ax=ax)
kmf.fit(kmfdata["Duration"][wins3], event_observed=kmfdata["Observed"][wins3], label="> 3")
kmf.plot(ax=ax)

plt.title("Survival separated by number of wins")
plt.ylim(0, 1)
plt.show()

"""
Cox Propotional Model using Age, Quickfire Wins, Wins, Highs and Lows to predict Out
"""
from lifelines import CoxTimeVaryingFitter
ctv = CoxTimeVaryingFitter()
ctv.fit(trainData[["Age", "QuickfireWins", "Wins", "Highs", "Lows", "Start", "End", "ID", "Out"]], id_col="ID", event_col="Out", start_col="Start", stop_col="End", show_progress=True)
ctv.print_summary()

#Get Hazards for specific episode
####EDIT THIS TO CHANGE WHICH SEASON/EPISODE YOU WANT TO APPLY THE MODEL TO#####
episode = 5
season = 13

predictData = allSeasonsByEpisode.loc[(allSeasonsByEpisode["Episode"] == episode) & (allSeasonsByEpisode["Season"] == season)]
## generate the relative risk with the model and merge it with the existing data
predictData["Partial Hazard"] = ctv.predict_partial_hazard(predictData)
predictData["Log Partial Hazard"] = ctv.predict_log_partial_hazard(predictData)
## clean up the data frame and display the ordered relative risks
predictData = predictData.sort_values(["Partial Hazard"], ascending = [True])
print("Model predictions for season " + str(season) + ", episode " + str(episode))
print(predictData[["FirstName", "LastName", "Partial Hazard", "Log Partial Hazard"]])

"""
What if we account for how many people are left in the competition
"""
ctv_compleft = CoxTimeVaryingFitter()
ctv_compleft.fit(trainData[["Age", "CompLeft", "QuickfireWins", "Wins", "Highs", "Lows", "Start", "End", "ID", "Out"]], id_col="ID", event_col="Out", start_col="Start", stop_col="End", show_progress=True)
ctv_compleft.print_summary()

## generate the relative risk with the model and merge it with the existing data
predictData["Partial Hazard"] = ctv_compleft.predict_partial_hazard(predictData)
predictData["Log Partial Hazard"] = ctv_compleft.predict_log_partial_hazard(predictData)
## clean up the data frame and display the ordered relative risks
predictData = predictData.sort_values(["Partial Hazard"], ascending = [True])
print("Model predictions for season " + str(season) + ", episode " + str(episode) + " if we take into account how many people are left in the competition")
print(predictData[["FirstName", "LastName", "Partial Hazard", "Log Partial Hazard"]])

"""
Now let's try a later episode in the season
"""
episode = 12
predictData = allSeasonsByEpisode.loc[(allSeasonsByEpisode["Episode"] == episode) & (allSeasonsByEpisode["Season"] == season)]
predictData["Partial Hazard"] = ctv.predict_partial_hazard(predictData)
predictData["Log Partial Hazard"] = ctv.predict_log_partial_hazard(predictData)
predictData = predictData.sort_values(["Partial Hazard"], ascending = [True])
print("Model predictions for season " + str(season) + ", episode " + str(episode))
print(predictData[["FirstName", "LastName", "Partial Hazard", "Log Partial Hazard"]])

predictData["Partial Hazard"] = ctv_compleft.predict_partial_hazard(predictData)
predictData["Log Partial Hazard"] = ctv_compleft.predict_log_partial_hazard(predictData)
predictData = predictData.sort_values(["Partial Hazard"], ascending = [True])
print("Model predictions for season " + str(season) + ", episode " + str(episode) + " if we take into account how many people are left in the competition")
print(predictData[["FirstName", "LastName", "Partial Hazard", "Log Partial Hazard"]])
