import os
import argparse
import azureml.core
import pandas as pd
import numpy as np
import pickle

from azureml.core import Experiment, Workspace, Run
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', type=str,
                    dest='data_dir', help='Directory of the data for training')
args = parser.parse_args()

print('Data dir is at:', args.data_dir)


# Load features and labels
temp_data = pd.read_csv(args.data_dir)
X, Y = temp_data[['ambient_temperature', 'ambient_humidity']].values, temp_data['anomaly'].values

# Get the run context to log metrics to the ML server
run = Run.get_context()

# Split data 65%-35% into training set and test set
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.25, random_state=0)


# Train a Logistic Regression on the training set
clf1 = LogisticRegression()
clf1 = clf1.fit(X_train, y_train)
print(clf1)

# Evaluate the test set
y_pred = clf1.predict(X_test)
report = classification_report(y_test, y_pred, output_dict=True)

# get accuracy
accuracy = report['accuracy']
print ("Accuracy is {}".format(accuracy))

# Log the metric on the server
run.log('accuracy', accuracy)

# Format the data to log as table in azure ML
df_report = pd.DataFrame(report).transpose()
report_dict = dict()
for col in df_report.columns:
    report_dict[col] = df_report[col].to_list()
report_dict['index'] = df_report.index.to_list()

# Log table of metrics
run.log_table(name='classification report', value=report_dict)

# Serialize the model and write to disk
os.makedirs('./outputs', exist_ok=True)
f = open('./outputs/model.pkl', 'wb')
pickle.dump(clf1, f)
f.close()
print ("Exported the model to model.pkl")