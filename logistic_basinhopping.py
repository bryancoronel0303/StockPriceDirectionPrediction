# -*- coding: utf-8 -*-
"""logistic_basinhopping

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SrrYKQAugCFHEhujGPGM_hB00HNJzOku

# 0. Install/Load Dependencies
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from scipy.optimize import basinhopping
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix

"""# 1. Data Pre-Processing, Feature Eng"""

df = pd.read_csv("/content/drive/MyDrive/spy.csv")

df['Average'] = df[['Open', 'Close', 'High', 'Low']].mean(axis=1)
df['HL_PCT'] = (df['High'] - df['Low']) / df['Low']
df['PCT_change'] = (df['Close'] - df['Open']) / df['Open']

df['Volume_pct_change'] = df['Volume'].pct_change() 
df["Target"] = (df["Close"] > df["Open"]).shift(periods=-1, fill_value=0).astype(int)

def macd(data, short=12, long=26, signal=9):
    exp1 = data['Close'].ewm(span=short, adjust=False).mean()
    exp2 = data['Close'].ewm(span=long, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line
def rsi(data, periods=14):
    delta = data['Close'].diff()
    gain, loss = delta.copy(), delta.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0

    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = -loss.rolling(window=periods).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
df['RSI'] = rsi(df)
df['MACD'], df['Signal'] = macd(df)

df = df.drop(['Date','Close', 'Volume', 'Year', 'Week'], axis=1).assign(Target=df.pop('Target'))
df.dropna(inplace=True)

X = df.drop(['Target'],axis=1)
y = df['Target']

# TimeSeriesSplit object
tscv = TimeSeriesSplit(n_splits=5)

for train_index, test_index in tscv.split(X):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    # Scale the features for the current train-test split
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

"""# 3. Implement Model"""

# Define the objective function to be optimized
def objective_function(params):
    #clf = LogisticRegression(penalty='none', solver='saga', fit_intercept=False, max_iter=1000, C=params[0], random_state=0)
    clf = LogisticRegression(C=params[0])
    clf.fit(X_train_scaled, y_train)
    accuracy = accuracy_score(y_test, clf.predict(X_test_scaled))
    # Return the negative accuracy (to maximize accuracy)
    return -accuracy
# initial guess for the params
x0 = [1.0]
# Define the bounds for the params
bounds = [(0.0001, 100)]
# optimize model
result = basinhopping(objective_function, x0, minimizer_kwargs={'bounds': bounds}, niter=250, disp=True)
# Get optimized parameters
optimized_params = result.x

optimized_params

"""# 4. Evaluate"""

#### BASE LOGISTIC
tscv = TimeSeriesSplit(n_splits=5)
accuracys = []
roc_aucs = []
f1_scores = []
precisions = []
recalls = []
conf_matrices = []

for train_index, test_index in tscv.split(X):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]

    # Scale the features for the current train-test split
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Create a logistic regression model with the optimized parameters
    clf = LogisticRegression()
    clf.fit(X_train_scaled, y_train)

    # Make predictions on the test set
    y_pred = clf.predict(X_test_scaled)
    y_pred_proba = clf.predict_proba(X_test_scaled)[:, 1]

    # Calculate performance metrics
    accuracys.append(accuracy_score(y_test, y_pred))
    roc_aucs.append(roc_auc_score(y_test, y_pred_proba))
    f1_scores.append(f1_score(y_test, y_pred))
    precisions.append(precision_score(y_test, y_pred))
    recalls.append(recall_score(y_test, y_pred))
    conf_matrices.append(confusion_matrix(y_test, y_pred))

    # Print the results for each fold
    # print("-------------")
    # print("Accuracy: ", accuracy)
    # print("ROC AUC Score: ", roc_auc)
    # print("F1 Score: ", f1)
    # print("Precision: ", precision)
    # print("Recall: ", recall)
    # print("Confusion Matrix: \n", conf_matrix)

print("-------------")
print("Average Accuracy: ", sum(accuracys) / len(accuracys))
print("Average ROC AUC Score: ", sum(roc_aucs) / len(roc_aucs))
print("Average F1 Score: ", sum(f1_scores) / len(f1_scores))
print("Average Precision: ", sum(precisions) / len(precisions))
print("Average Recall: ", sum(recalls) / len(recalls))

#### w/ C chosen from basinhopping
tscv = TimeSeriesSplit(n_splits=5)
accuracys = []
roc_aucs = []
f1_scores = []
precisions = []
recalls = []
conf_matrices = []

for train_index, test_index in tscv.split(X):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]

    # Scale the features for the current train-test split
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Create a logistic regression model with the optimized parameters
    clf = LogisticRegression(C=optimized_params[0])
    clf.fit(X_train_scaled, y_train)

    # Make predictions on the test set
    y_pred = clf.predict(X_test_scaled)
    y_pred_proba = clf.predict_proba(X_test_scaled)[:, 1]

    # Calculate performance metrics
    accuracys.append(accuracy_score(y_test, y_pred))
    roc_aucs.append(roc_auc_score(y_test, y_pred_proba))
    f1_scores.append(f1_score(y_test, y_pred))
    precisions.append(precision_score(y_test, y_pred))
    recalls.append(recall_score(y_test, y_pred))
    conf_matrices.append(confusion_matrix(y_test, y_pred))
print("-------------")
print("Average Accuracy: ", sum(accuracys) / len(accuracys))
print("Average ROC AUC Score: ", sum(roc_aucs) / len(roc_aucs))
print("Average F1 Score: ", sum(f1_scores) / len(f1_scores))
print("Average Precision: ", sum(precisions) / len(precisions))
print("Average Recall: ", sum(recalls) / len(recalls))
        # # Future predictions
        # future_dates = 1  # Set the number of days to predict
        # X_future = X.iloc[test_index[-future_dates:]]
        # X_future_scaled = scaler.transform(X_future)  # Scale the future data using the same scaler
        # future_predictions = best_model.predict(X_future_scaled)

        # # Convert predicted directions to gain/loss
        # future_directions = ['gain' if direction == 1 else 'loss' for direction in future_predictions]

        # print("Future Predictions: ", future_directions)
        # print("-------------")
        # print("")

