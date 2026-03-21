# NYC Flights Dashboard

An interactive Streamlit dashboard for exploring flight operations in New York City during 2023.

Our project focuses on flights departing from **JFK, LGA, and EWR** and looks at important aspects such as airport traffic, airline performance, delays, aircraft capacity, plane characteristics, and the effect of weather on flights.

## Dashboard Preview

Here is a quick look at the dashboard:

<p align="center">
  <img src="demo.gif" alt="Dashboard preview" width="900"/>
</p>

## What the Dashboard Covers

The dashboard helps explore and compare different parts of NYC flight activity, including:

- airport traffic and route activity
- airline performance
- delays and possible causes
- aircraft capacity and estimated passenger throughput
- plane model characteristics
- weather conditions and their relationship with delays

## Dashboard Pages

The dashboard includes the following pages:

- **General Overview** – summary KPIs, busiest routes, destinations, and overall flight patterns  
- **Airport Comparison** – comparison of JFK, LGA, and EWR in terms of traffic, delays, cancellations, and weather sensitivity  
- **Capacity Aircraft Analysis** – estimated seat capacity by airport, airline, route, and month  
- **Carrier Performance** – comparison of airlines based on on-time rate, delays, cancellations, and airport dominance  
- **Delay Analysis** – delay distributions, routes, airlines, time-of-day patterns, and possible delay factors  
- **Plane Models Analysis** – manufacturers, engine types, aircraft models, and fleet characteristics  
- **Weather Analysis** – how wind, precipitation, visibility, and bad weather conditions relate to delays  

## Project Structure

Below is the **essential idea** of the project structure:

```bash
project-flights-1/
├── data/                  #data used for the project
├── part1/                 # initial airport analysis
├── part3/                 # analysis and flight-related statistics
├── part4/                 # data cleaning, validation, and additional analytical modules.
├── part5/                 # dashboard implementation
│   ├── dashboard_features/
│   └── pages/
│   └── general.py
├──                
├── requirements.txt        # project dependencies
└── README.md

```

## Instructions

Follow these steps to run the NYC Flights Dashboard on your computer.

### 1. Clone the repository

Download the project from GitHub and move into the project folder.

```bash
git clone <https://github.com/Christinaliti/Project-flights-1.git>
cd <project-flights-1>
```

## 3. Install the required dependencies

Install all the required Python packages using the requirements file.

```bash
pip install -r requirements.txt
```

## 4. Run the Streamlit dashboard

Start the dashboard with the following command:

```bash
 streamlit run part5/general.py
```

### 5. Open the dashboard

After running the command, Streamlit will display  the result in a local URL:

```
http://localhost:8501
```


### 6. Stop the application

To stop the dashboard, press:

```
Ctrl + C
```

in the terminal.