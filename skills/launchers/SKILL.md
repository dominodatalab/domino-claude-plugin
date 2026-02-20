---
name: domino-launchers
description: Create Domino Launchers - parameterized web forms for self-service job execution. Enable business users to run analyses, generate reports, and trigger batch predictions without coding. Covers parameter types, email notifications, result delivery, and access control. Use when building self-service data products or enabling non-technical users.
---

# Domino Launchers Skill

## Description
This skill helps users create and use Domino Launchers - web forms that allow non-technical users to run parameterized jobs and receive results.

## Activation
Activate this skill when users want to:
- Create self-service data products
- Build parameterized job interfaces
- Enable business users to run analyses
- Generate reports on demand
- Share reproducible workflows

## What is a Launcher?

A Launcher is:
- **Web Form**: UI for entering parameters
- **Job Trigger**: Runs a script with user inputs
- **Results Delivery**: Sends output via email/dashboard
- **Self-Service**: Business users can run without coding

## Use Cases

- **Report Generation**: Parameterized business reports
- **Batch Predictions**: Score data on demand
- **Data Exports**: Custom data extracts
- **Analysis Requests**: Ad-hoc analytics
- **Model Testing**: Test models with different inputs

## Creating a Launcher

### Via Domino UI
1. Go to your project
2. Navigate to **Deployments** > **Launchers**
3. Click **New Launcher**
4. Configure:
   - **Name**: Descriptive name
   - **Description**: What the launcher does
   - **Command**: Script to run
   - **Parameters**: Input fields
   - **Hardware Tier**: Resources
   - **Environment**: Compute environment

### Launcher Script (Python)
```python
# generate_report.py
import argparse
import pandas as pd

# Parse launcher parameters
parser = argparse.ArgumentParser()
parser.add_argument('--start-date', required=True)
parser.add_argument('--end-date', required=True)
parser.add_argument('--region', default='all')
args = parser.parse_args()

# Generate report
df = generate_report(args.start_date, args.end_date, args.region)

# Save results (will be available to launcher user)
df.to_csv('/mnt/results/report.csv', index=False)
df.to_html('/mnt/results/report.html', index=False)
```

### Launcher Script (R)
```r
# launcher.R
args <- commandArgs(trailingOnly = TRUE)
a <- as.integer(args[1])
b <- as.integer(args[2])

if (is.na(a)) {
  print("A is not a number")
} else if (is.na(b)) {
  print("B is not a number")
} else {
  paste("The sum of", a, "and", b, "is:", a + b)
}
```

Command: `launcher.R ${A} ${B}`

### Launcher Command
```bash
# Python script with named arguments
python generate_report.py --start-date ${start_date} --end-date ${end_date} --region ${region}

# Python script with positional arguments
my_script.py -x=1 ${file} ${start_date}

# R script with positional arguments
launcher.R ${A} ${B}
```

**Note:** Parameter values are enclosed in single quotes, preserving special characters. File parameters pass the file path. Multi-select parameters pass comma-separated values.

## Parameter Types

### Text Input
```yaml
name: customer_name
type: text
label: Customer Name
required: true
default: ""
```

### Dropdown/Select
```yaml
name: region
type: select
label: Region
options:
  - North America
  - Europe
  - Asia Pacific
default: North America
```

### Date Picker
```yaml
name: start_date
type: date
label: Start Date
required: true
```

### Number
```yaml
name: quantity
type: number
label: Quantity
min: 1
max: 1000
default: 100
```

### File Upload
```yaml
name: input_file
type: file
label: Input File
accept: .csv,.xlsx
```

## Generating Results

### File-Based Results
Any files created in `/mnt/results/` are available as results:

```python
# Save multiple output formats
df.to_csv('/mnt/results/data.csv')
df.to_excel('/mnt/results/data.xlsx')
fig.savefig('/mnt/results/chart.png')
```

### HTML Email Content
Create `email.html` for custom email body:
```python
# Generate HTML for email
html_content = f"""
<html>
<body>
<h1>Report for {args.start_date} to {args.end_date}</h1>
<p>Summary: {summary}</p>
{df.to_html()}
</body>
</html>
"""

with open('/mnt/results/email.html', 'w') as f:
    f.write(html_content)
```

### Rich Reports
Use notebooks for rich reports:
```python
# Use papermill to execute parameterized notebook
import papermill as pm

pm.execute_notebook(
    'report_template.ipynb',
    '/mnt/results/report.ipynb',
    parameters={
        'start_date': args.start_date,
        'end_date': args.end_date
    }
)
```

## Notifications

### Email Configuration
Configure notification recipients:
1. In launcher settings
2. Add email addresses
3. Results sent automatically on completion

### Email Contents
- Link to results in Domino
- Attached files (if enabled)
- Custom HTML body (if email.html created)

## Access Control

### Who Can Run Launchers
- **Contributors**: Can create and run launchers
- **Launcher Users**: Can run launchers only
- **Results Consumers**: Can view results only

### Setting Permissions
1. Go to Project Settings
2. Add users with appropriate roles
3. Share launcher URL with users

## Running a Launcher

### Via UI
1. Go to launcher page
2. Fill in parameters
3. Click **Run**
4. Wait for results (email notification)

### Via API
```python
import requests

response = requests.post(
    "https://your-domino.com/v4/launchers/{launcher_id}/run",
    headers={"X-Domino-Api-Key": "YOUR_API_KEY"},
    json={
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "region": "North America"
        }
    }
)

run_id = response.json()["runId"]
```

## Viewing Results

### Via Email
Results link sent to configured recipients.

### Via Jobs Dashboard
Each launcher run creates a job:
1. Go to **Jobs** in project
2. Find the launcher job
3. View results in job details

### Programmatic Access
```python
# Get launcher run results
results = domino.runs_get_results(run_id)
```

## Example: Scoring Launcher

### Script (score_data.py)
```python
import argparse
import pandas as pd
import joblib

parser = argparse.ArgumentParser()
parser.add_argument('--input-file', required=True)
parser.add_argument('--output-format', default='csv')
args = parser.parse_args()

# Load model
model = joblib.load('/mnt/artifacts/model.joblib')

# Load and score data
df = pd.read_csv(args.input_file)
predictions = model.predict(df)
df['prediction'] = predictions

# Save results
if args.output_format == 'csv':
    df.to_csv('/mnt/results/predictions.csv', index=False)
else:
    df.to_excel('/mnt/results/predictions.xlsx', index=False)
```

### Launcher Configuration
```yaml
name: Score Customer Data
command: python score_data.py --input-file ${input_file} --output-format ${output_format}
parameters:
  - name: input_file
    type: file
    label: Customer Data (CSV)
    required: true
  - name: output_format
    type: select
    label: Output Format
    options: [csv, xlsx]
    default: csv
```

## Best Practices

### 1. Clear Parameter Names
Use descriptive labels users understand.

### 2. Input Validation
```python
# Validate inputs in script
if args.end_date < args.start_date:
    raise ValueError("End date must be after start date")
```

### 3. Progress Logging
```python
print("Loading data...")
print(f"Processing {len(df)} records...")
print("Generating report...")
print("Complete!")
```

### 4. Error Handling
```python
try:
    process_data()
except Exception as e:
    # Save error message as result
    with open('/mnt/results/error.txt', 'w') as f:
        f.write(f"Error: {str(e)}")
    raise
```

### 5. Documentation
Include help text in launcher description.

## Troubleshooting

### Launcher Fails
- Check script runs manually first
- Verify file paths are correct
- Review job logs for errors

### No Email Received
- Check email addresses configured
- Verify email server settings (admin)
- Check spam folder

### Wrong Results
- Verify parameter passing
- Check variable substitution syntax
- Test with known inputs

## Documentation Reference
- [Use Launchers](https://docs.dominodatalab.com/en/latest/user_guide/f4e1e3/use-launchers/)
