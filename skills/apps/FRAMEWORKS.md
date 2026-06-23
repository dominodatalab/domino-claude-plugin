# Framework-Specific Configurations for Domino Apps

This guide covers configuration for various web frameworks when deploying to Domino Data Lab.

## Streamlit

### Basic app.sh

```bash
#!/bin/bash
set -e

streamlit run app.py \
    --server.port 8888 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
```

### With Custom Configuration

```bash
#!/bin/bash
set -e

# Create Streamlit config directory
mkdir -p ~/.streamlit

# Write config file
cat > ~/.streamlit/config.toml << 'EOF'
[server]
port = 8888
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1976d2"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f5f5f5"
textColor = "#212121"
EOF

streamlit run app.py
```

### Example Streamlit App

```python
# app.py
import streamlit as st
import os
import requests

st.set_page_config(
    page_title="ML Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("ML Model Dashboard")

# Display Domino environment info
with st.expander("Environment Info"):
    st.write(f"Project: {os.environ.get('DOMINO_PROJECT_NAME', 'N/A')}")
    st.write(f"User: {os.environ.get('DOMINO_STARTING_USERNAME', 'N/A')}")

# Model prediction interface
st.header("Make Prediction")

feature1 = st.number_input("Feature 1", value=0.0)
feature2 = st.number_input("Feature 2", value=0.0)

if st.button("Predict"):
    model_url = os.environ.get('MODEL_API_URL')
    model_token = os.environ.get('MODEL_API_TOKEN')

    if model_url and model_token:
        response = requests.post(
            model_url,
            headers={
                'Authorization': f'Bearer {model_token}',
                'Content-Type': 'application/json'
            },
            json={'data': {'feature1': feature1, 'feature2': feature2}}
        )
        st.json(response.json())
    else:
        st.error("Model API not configured")
```

## Dash (Plotly)

### Basic app.sh

```bash
#!/bin/bash
set -e

python app.py
```

### Example Dash App

```python
# app.py
import os
import dash
from dash import html, dcc, callback, Input, Output
import requests

# IMPORTANT: Use routes_pathname_prefix='/' for proper routing inside Domino
app = dash.Dash(__name__, routes_pathname_prefix='/')

app.layout = html.Div([
    html.H1("ML Model Dashboard"),

    html.Div([
        html.Label("Feature 1:"),
        dcc.Input(id='feature1', type='number', value=0),

        html.Label("Feature 2:"),
        dcc.Input(id='feature2', type='number', value=0),

        html.Button('Predict', id='predict-btn', n_clicks=0),
    ]),

    html.Div(id='prediction-output'),

    # Environment info
    html.Div([
        html.P(f"Project: {os.environ.get('DOMINO_PROJECT_NAME', 'N/A')}"),
        html.P(f"User: {os.environ.get('DOMINO_STARTING_USERNAME', 'N/A')}"),
    ], style={'marginTop': '20px', 'color': 'gray'})
])

@callback(
    Output('prediction-output', 'children'),
    Input('predict-btn', 'n_clicks'),
    Input('feature1', 'value'),
    Input('feature2', 'value'),
    prevent_initial_call=True
)
def predict(n_clicks, feature1, feature2):
    model_url = os.environ.get('MODEL_API_URL')
    model_token = os.environ.get('MODEL_API_TOKEN')

    if not model_url or not model_token:
        return html.P("Model API not configured", style={'color': 'red'})

    try:
        response = requests.post(
            model_url,
            headers={
                'Authorization': f'Bearer {model_token}',
                'Content-Type': 'application/json'
            },
            json={'data': {'feature1': feature1, 'feature2': feature2}}
        )
        return html.Pre(str(response.json()))
    except Exception as e:
        return html.P(f"Error: {str(e)}", style={'color': 'red'})

if __name__ == '__main__':
    # CRITICAL: Bind to 0.0.0.0:8888 for Domino
    app.run_server(
        host='0.0.0.0',
        port=8888,
        debug=False
    )
```

## Flask

### Basic app.sh

```bash
#!/bin/bash
set -e

python app.py
```

### Example Flask App

```python
# app.py
import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
        project=os.environ.get('DOMINO_PROJECT_NAME', 'N/A'),
        user=os.environ.get('DOMINO_STARTING_USERNAME', 'N/A')
    )

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    model_url = os.environ.get('MODEL_API_URL')
    model_token = os.environ.get('MODEL_API_TOKEN')

    if not model_url or not model_token:
        return jsonify({'error': 'Model API not configured'}), 500

    try:
        response = requests.post(
            model_url,
            headers={
                'Authorization': f'Bearer {model_token}',
                'Content-Type': 'application/json'
            },
            json={'data': data}
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # CRITICAL: Bind to 0.0.0.0:8888 for Domino
    app.run(
        host='0.0.0.0',
        port=8888,
        debug=False
    )
```

### Flask with Gunicorn (Production)

```bash
#!/bin/bash
set -e

pip install gunicorn

gunicorn app:app \
    --bind 0.0.0.0:8888 \
    --workers 4 \
    --timeout 120
```

## Gradio

### Basic app.sh

```bash
#!/bin/bash
set -e

python app.py
```

### Example Gradio App

```python
# app.py
import os
import gradio as gr
import requests

def predict(feature1, feature2):
    model_url = os.environ.get('MODEL_API_URL')
    model_token = os.environ.get('MODEL_API_TOKEN')

    if not model_url or not model_token:
        return "Model API not configured"

    try:
        response = requests.post(
            model_url,
            headers={
                'Authorization': f'Bearer {model_token}',
                'Content-Type': 'application/json'
            },
            json={'data': {'feature1': feature1, 'feature2': feature2}}
        )
        return str(response.json())
    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.Interface(
    fn=predict,
    inputs=[
        gr.Number(label="Feature 1"),
        gr.Number(label="Feature 2")
    ],
    outputs=gr.Textbox(label="Prediction"),
    title="ML Model Interface",
    description=f"Project: {os.environ.get('DOMINO_PROJECT_NAME', 'N/A')}"
)

if __name__ == '__main__':
    # CRITICAL: Bind to 0.0.0.0:8888 for Domino
    demo.launch(
        server_name='0.0.0.0',
        server_port=8888,
        share=False
    )
```

## Panel (HoloViz)

### Basic app.sh

```bash
#!/bin/bash
set -e

panel serve app.py \
    --address 0.0.0.0 \
    --port 8888 \
    --allow-websocket-origin="*"
```

### Example Panel App

```python
# app.py
import os
import panel as pn
import requests

pn.extension()

feature1_input = pn.widgets.FloatInput(name='Feature 1', value=0)
feature2_input = pn.widgets.FloatInput(name='Feature 2', value=0)
predict_button = pn.widgets.Button(name='Predict', button_type='primary')
output = pn.pane.Markdown("Click Predict to get results")

def predict(event):
    model_url = os.environ.get('MODEL_API_URL')
    model_token = os.environ.get('MODEL_API_TOKEN')

    if not model_url or not model_token:
        output.object = "**Error:** Model API not configured"
        return

    try:
        response = requests.post(
            model_url,
            headers={
                'Authorization': f'Bearer {model_token}',
                'Content-Type': 'application/json'
            },
            json={'data': {
                'feature1': feature1_input.value,
                'feature2': feature2_input.value
            }}
        )
        output.object = f"**Result:** {response.json()}"
    except Exception as e:
        output.object = f"**Error:** {str(e)}"

predict_button.on_click(predict)

layout = pn.Column(
    "# ML Model Dashboard",
    f"Project: {os.environ.get('DOMINO_PROJECT_NAME', 'N/A')}",
    feature1_input,
    feature2_input,
    predict_button,
    output
)

layout.servable()
```

## FastAPI

### Basic app.sh

```bash
#!/bin/bash
set -e

uvicorn app:app --host 0.0.0.0 --port 8888
```

### Example FastAPI App with Static Files

```python
# app.py
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "project": os.environ.get('DOMINO_PROJECT_NAME', 'N/A'),
        "user": os.environ.get('DOMINO_STARTING_USERNAME', 'N/A')
    })

@app.post("/predict")
async def predict(data: dict):
    model_url = os.environ.get('MODEL_API_URL')
    model_token = os.environ.get('MODEL_API_TOKEN')

    if not model_url or not model_token:
        return {"error": "Model API not configured"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            model_url,
            headers={
                'Authorization': f'Bearer {model_token}',
                'Content-Type': 'application/json'
            },
            json={'data': data}
        )
        return response.json()

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Shiny (R)

### Option 1: Inline R Script

```r
# app.R
shiny::runApp("./", port = 8888, host = "0.0.0.0")
```

### Option 2: Shell Script (app.sh)

```bash
#!/bin/bash
set -e

R -e 'shiny::runApp("./", port=8888, host="0.0.0.0")'
```

### Example Shiny App

```r
# app.R
library(shiny)

ui <- fluidPage(
  titlePanel("ML Model Dashboard"),

  sidebarLayout(
    sidebarPanel(
      numericInput("feature1", "Feature 1:", value = 0),
      numericInput("feature2", "Feature 2:", value = 0),
      actionButton("predict", "Predict")
    ),

    mainPanel(
      h4("Prediction Result:"),
      verbatimTextOutput("result"),
      hr(),
      p(paste("Project:", Sys.getenv("DOMINO_PROJECT_NAME", "N/A"))),
      p(paste("User:", Sys.getenv("DOMINO_STARTING_USERNAME", "N/A")))
    )
  )
)

server <- function(input, output, session) {
  observeEvent(input$predict, {
    model_url <- Sys.getenv("MODEL_API_URL")
    model_token <- Sys.getenv("MODEL_API_TOKEN")

    if (model_url != "" && model_token != "") {
      library(httr)
      response <- POST(
        model_url,
        add_headers(
          "Authorization" = paste("Bearer", model_token),
          "Content-Type" = "application/json"
        ),
        body = list(data = list(
          feature1 = input$feature1,
          feature2 = input$feature2
        )),
        encode = "json"
      )
      output$result <- renderText({ content(response, "text") })
    } else {
      output$result <- renderText({ "Model API not configured" })
    }
  })
}

shinyApp(ui = ui, server = server)
```

### Running the Shiny App

```bash
# app.sh
#!/bin/bash
set -e

# Run the Shiny app on required port
R -e 'shiny::runApp("./", port=8888, host="0.0.0.0")'
```

**Note:** Port selection is flexible; port 8888 is no longer required. You can use any port your application prefers.

## Common Requirements

### requirements.txt Examples

**Streamlit:**
```
streamlit>=1.28.0
requests>=2.28.0
pandas>=2.0.0
```

**Dash:**
```
dash>=2.14.0
requests>=2.28.0
pandas>=2.0.0
plotly>=5.18.0
```

**Flask:**
```
flask>=3.0.0
gunicorn>=21.0.0
requests>=2.28.0
```

**Gradio:**
```
gradio>=4.0.0
requests>=2.28.0
```

## Environment Variables

All frameworks should access these Domino-provided variables:

| Variable | Description |
|----------|-------------|
| `DOMINO_PROJECT_NAME` | Current project name |
| `DOMINO_PROJECT_OWNER` | Project owner username |
| `DOMINO_RUN_ID` | Current run identifier |
| `DOMINO_STARTING_USERNAME` | User who started the app |

Custom variables for model integration:

| Variable | Description |
|----------|-------------|
| `MODEL_API_URL` | Endpoint URL for model predictions |
| `MODEL_API_TOKEN` | Bearer token for API authentication |
