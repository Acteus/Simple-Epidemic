import streamlit as st
import pandas as pd
import time
import altair as alt
from simulation import EpidemicSimulation, SimulationConfig

# Page Configuration
st.set_page_config(
    page_title="Epidemic Simulation",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "premium" look
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

st.title("🦠 Interactive Epidemic Simulation")

# Sidebar Parameters
st.sidebar.header("⚙️ Simulation Parameters")

with st.sidebar.expander("Population Settings", expanded=True):
    N = st.slider("Population Size (N)", 50, 1000, 200, help="Total number of agents")
    grid_size = st.slider("Grid Size", 20.0, 200.0, 100.0, help="Size of the simulation world")

with st.sidebar.expander("Disease Characteristics", expanded=True):
    beta = st.slider("Infection Rate (β)", 0.0, 5.0, 1.0, help="Transmission probability per contact")
    
    st.markdown("**Incubation Period (Days)**")
    col1, col2 = st.columns(2)
    incubation_mean = col1.slider("Mean", 1.0, 14.0, 5.0, key="inc_mean")
    incubation_std = col2.slider("Std Dev", 0.1, 5.0, 2.0, key="inc_std")
    
    st.markdown("**Infectious Period (Days)**")
    col3, col4 = st.columns(2)
    infectious_mean = col3.slider("Mean", 1.0, 21.0, 7.0, key="inf_mean")
    infectious_std = col4.slider("Std Dev", 0.1, 5.0, 3.0, key="inf_std")
    
    mortality_rate = st.slider("Mortality Rate (CFR)", 0.0, 0.5, 0.02, help="Probability of death given infection")

with st.sidebar.expander("Interventions & Mobility", expanded=False):
    vax_rate = st.slider("Vaccination Rate", 0.0, 0.1, 0.0, format="%.3f", help="Daily vaccination rate (S->R)")
    detection_prob = st.slider("Detection Probability", 0.0, 1.0, 0.0, help="Probability of detecting an infectious case")
    isolation_compliance = st.slider("Isolation Compliance", 0.0, 1.0, 0.8, help="Probability of complying with isolation if detected")
    
    st.markdown("---")
    home_attraction = st.slider("Home Attraction", 0.0, 0.5, 0.05, help="Strength of pull towards home location")
    random_force = st.slider("Random Movement", 0.0, 2.0, 1.0, help="Intensity of random walk")

# Session State Management
if 'config' not in st.session_state:
    st.session_state.config = SimulationConfig(
        N=N, grid_size=grid_size, beta=beta, 
        incubation_mean=incubation_mean, incubation_std=incubation_std,
        infectious_mean=infectious_mean, infectious_std=infectious_std,
        mortality_rate=mortality_rate, vax_rate=vax_rate,
        detection_prob=detection_prob, isolation_compliance=isolation_compliance,
        home_attraction=home_attraction, random_force=random_force
    )

if 'sim' not in st.session_state:
    st.session_state.sim = EpidemicSimulation(st.session_state.config)

if 'running' not in st.session_state:
    st.session_state.running = False
if 'day' not in st.session_state:
    st.session_state.day = 0.0

# Construct current config from UI
current_config = SimulationConfig(
    N=N, grid_size=grid_size, beta=beta, 
    incubation_mean=incubation_mean, incubation_std=incubation_std,
    infectious_mean=infectious_mean, infectious_std=infectious_std,
    mortality_rate=mortality_rate, vax_rate=vax_rate,
    detection_prob=detection_prob, isolation_compliance=isolation_compliance,
    home_attraction=home_attraction, random_force=random_force
)

# Control Buttons
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("▶️ Start"):
    st.session_state.running = True
if col2.button("⏸️ Stop"):
    st.session_state.running = False
if col3.button("🔄 Reset"):
    st.session_state.running = False
    st.session_state.config = current_config
    st.session_state.sim = EpidemicSimulation(st.session_state.config)
    st.session_state.day = 0.0

# Apply dynamic parameter updates if running
if st.session_state.running:
    # Update mutable parameters
    st.session_state.sim.config.beta = beta
    st.session_state.sim.config.incubation_mean = incubation_mean
    st.session_state.sim.config.incubation_std = incubation_std
    st.session_state.sim.config.infectious_mean = infectious_mean
    st.session_state.sim.config.infectious_std = infectious_std
    st.session_state.sim.config.mortality_rate = mortality_rate
    st.session_state.sim.config.vax_rate = vax_rate
    st.session_state.sim.config.detection_prob = detection_prob
    st.session_state.sim.config.isolation_compliance = isolation_compliance
    st.session_state.sim.config.home_attraction = home_attraction
    st.session_state.sim.config.random_force = random_force

# Main Layout
# Metrics
stats = st.session_state.sim.stats
current_s = stats["S"][-1] if stats["S"] else N - 1
current_e = stats["E"][-1] if stats["E"] else 0
current_i = stats["I"][-1] if stats["I"] else 1
current_r = stats["R"][-1] if stats["R"] else 0
current_d = stats["D"][-1] if stats["D"] else 0

# Calculate Rt (last value)
current_rt = st.session_state.sim.rt_history[-1] if st.session_state.sim.rt_history else 0.0

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Susceptible", current_s, delta_color="inverse")
m2.metric("Exposed", current_e, delta_color="inverse")
m3.metric("Infected", current_i, delta_color="inverse")
m4.metric("Recovered", current_r, delta_color="normal")
m5.metric("Deceased", current_d, delta_color="off")
m6.metric("Est. Rt", f"{current_rt:.2f}", delta_color="off")

# Visualization Columns
viz_col, chart_col = st.columns([1, 1])

with viz_col:
    st.subheader(f"Simulation Grid (Day {st.session_state.day:.1f})")
    agents = st.session_state.sim.get_agent_data()
    df_agents = pd.DataFrame(agents)
    
    # Custom color scale
    domain = ["S", "E", "I", "R", "D"]
    range_ = ["#3498db", "#f1c40f", "#e74c3c", "#2ecc71", "#34495e"] # Blue, Yellow, Red, Green, Dark Grey
    
    chart = alt.Chart(df_agents).mark_circle(size=60).encode(
        x=alt.X('x', scale=alt.Scale(domain=[0, grid_size]), axis=None),
        y=alt.Y('y', scale=alt.Scale(domain=[0, grid_size]), axis=None),
        color=alt.Color('state', scale=alt.Scale(domain=domain, range=range_), legend=alt.Legend(title="State")),
        tooltip=['id', 'state', 'days_in_state', 'is_isolated']
    ).properties(
        width=400,
        height=400
    ).configure_view(
        strokeWidth=0
    )
    
    st.altair_chart(chart, use_container_width=True)

with chart_col:
    st.subheader("Population Dynamics")
    if st.session_state.day > 0:
        stats_df = pd.DataFrame(st.session_state.sim.stats)
        # Create a time axis based on steps and dt
        steps = range(len(stats_df))
        stats_df['Day'] = [s * st.session_state.sim.config.dt for s in steps]
        
        stats_long = stats_df.melt('Day', var_name='State', value_name='Count')
        
        line_chart = alt.Chart(stats_long).mark_line().encode(
            x='Day',
            y='Count',
            color=alt.Color('State', scale=alt.Scale(domain=domain, range=range_)),
            tooltip=['Day', 'State', 'Count']
        ).properties(
            height=300
        )
        st.altair_chart(line_chart, use_container_width=True)
        
        # Rt Chart
        st.subheader("Effective Reproduction Number (Rt)")
        rt_df = pd.DataFrame({'Day': stats_df['Day'], 'Rt': st.session_state.sim.rt_history})
        rt_chart = alt.Chart(rt_df).mark_line(color='purple').encode(
            x='Day',
            y='Rt',
            tooltip=['Day', 'Rt']
        ).properties(
            height=200
        )
        # Add a reference line at Rt=1
        rule = alt.Chart(pd.DataFrame({'Rt': [1.0]})).mark_rule(color='red', strokeDash=[5, 5]).encode(y='Rt')
        
        st.altair_chart(rt_chart + rule, use_container_width=True)
        
    else:
        st.info("Start the simulation to see the chart.")

# Simulation Loop
if st.session_state.running:
    st.session_state.sim.step()
    st.session_state.day += st.session_state.sim.config.dt
    time.sleep(0.02) # Faster updates
    st.rerun()
