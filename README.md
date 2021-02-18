# COVID Dashboard

## Setup

### Run the code

You will need to install the app's dependencies in a virtual envrionment to be able to run the app.

1. Navigate to the directory where you would like to clone this repo. For example, if I'm currently in my home directory want to clone the repo in a folder called Documents/Projects, I will run: ```cd Documents/Projects```
2. Clone the repo using the following command: ```git clone https://github.com/jolenezheng/COVIDDashboard.git```
3. Run the following commands once you are in the root of your project
```bash
python -m venv venv
source venv/bin/activate  # Windows: \venv\scripts\activate
pip install -r requirements.txt
```
4. Then run the app using: ```python app.py```
5. You should now see the app running at: http://localhost:8050/