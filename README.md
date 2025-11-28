# 🦠 Simple Epidemic Simulation

An interactive, agent-based epidemic simulation built with Streamlit. This project models disease spread through a population using spatial dynamics, allowing you to visualize how epidemics evolve over time with customizable parameters.

## Features

- **Agent-Based Modeling**: Each individual in the population is modeled as an autonomous agent with position, velocity, and health state
- **SEIRD Model**: Implements Susceptible → Exposed → Infected → Recovered/Deceased disease progression
- **Spatial Dynamics**: Agents move in a 2D space with home attraction and random walk behavior
- **Real-time Visualization**: Interactive Streamlit dashboard with live simulation grid and population dynamics charts
- **Interventions**: Model vaccination, case detection, and isolation measures
- **Effective Reproduction Number (Rt)**: Tracks the real-time reproduction number throughout the simulation
- **Customizable Parameters**: Adjust population size, disease characteristics, mobility patterns, and intervention strategies

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/Simple-Epidemic.git
cd Simple-Epidemic
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default web browser. Use the sidebar to adjust simulation parameters:

### Population Settings
- **Population Size (N)**: Total number of agents (50-1000)
- **Grid Size**: Size of the simulation world (20-200)

### Disease Characteristics
- **Infection Rate (β)**: Transmission probability per contact (0-5)
- **Incubation Period**: Mean and standard deviation in days
- **Infectious Period**: Mean and standard deviation in days
- **Mortality Rate (CFR)**: Case fatality rate (0-0.5)

### Interventions & Mobility
- **Vaccination Rate**: Daily rate of vaccination (S→R)
- **Detection Probability**: Probability of detecting an infectious case
- **Isolation Compliance**: Probability of complying with isolation if detected
- **Home Attraction**: Strength of pull towards home location
- **Random Movement**: Intensity of random walk

### Controls
- **▶️ Start**: Begin the simulation
- **⏸️ Stop**: Pause the simulation
- **🔄 Reset**: Reset the simulation with current parameters

## Project Structure

```
Simple-Epidemic/
├── app.py              # Streamlit web application
├── simulation.py       # Core simulation engine and agent logic
├── test_simulation.py  # Unit tests for simulation
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Simulation Model

### Agent States
- **S (Susceptible)**: Healthy and can be infected
- **E (Exposed)**: Infected but not yet infectious (incubation period)
- **I (Infected)**: Infectious and can spread the disease
- **R (Recovered)**: Recovered and immune
- **D (Deceased)**: Died from the disease

### Movement Model
Agents move using a combination of:
- **Home Attraction**: Agents are pulled back toward their home location
- **Random Walk**: Brownian motion adds stochastic movement
- **Velocity Damping**: Prevents agents from moving too fast

### Infection Model
- Infections occur when susceptible agents are within the interaction radius of infectious agents
- Transmission probability depends on:
  - Base infection rate (β)
  - Infectious agent's infectiousness (heterogeneous)
  - Susceptible agent's susceptibility (heterogeneous)
  - Time step (dt)

### Interventions
- **Vaccination**: Converts susceptible agents directly to recovered
- **Detection & Isolation**: Detected infectious agents are isolated and cannot spread disease

## Testing

Run the test suite:
```bash
python -m pytest test_simulation.py
```

Or using unittest:
```bash
python test_simulation.py
```

## Requirements

- Python 3.7+
- numpy
- matplotlib
- streamlit
- pandas
- altair (installed with streamlit)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

This simulation is inspired by epidemiological models and agent-based modeling techniques used in disease spread research.

