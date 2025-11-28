import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class SimulationConfig:
    N: int = 200
    grid_size: float = 100.0
    beta: float = 1.0
    
    # Explicit periods (lognormal/gamma distributions)
    incubation_mean: float = 5.0
    incubation_std: float = 2.0
    infectious_mean: float = 7.0
    infectious_std: float = 3.0
    
    mortality_rate: float = 0.02 # Probability of death at end of infection
    
    vax_rate: float = 0.0
    interaction_radius: float = 2.0
    dt: float = 0.5 # Smaller step for better mobility resolution
    
    # Mobility
    home_attraction: float = 0.05
    random_force: float = 1.0
    
    # Interventions
    isolation_compliance: float = 0.0
    detection_prob: float = 0.0

@dataclass
class Agent:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    home_x: float
    home_y: float
    infectiousness: float = 1.0
    susceptibility: float = 1.0
    state: str = "S"  # S, E, I, R, D
    state_timer: float = 0.0 # Time remaining in current state (for E and I)
    days_in_state: float = 0.0
    is_isolated: bool = False
    next_state: str = None
    next_timer: float = 0.0
    
    def move(self, grid_size: float, dt: float, home_attraction: float, random_force: float):
        if self.state == "D" or self.is_isolated:
            return

        # 1. Attraction to home
        dx = self.home_x - self.x
        dy = self.home_y - self.y
        self.vx += dx * home_attraction * dt
        self.vy += dy * home_attraction * dt
        
        # 2. Random walk (Brownian motion)
        self.vx += random.uniform(-1, 1) * random_force * dt
        self.vy += random.uniform(-1, 1) * random_force * dt
        
        # 3. Damping (friction) to prevent exploding speeds
        self.vx *= 0.95
        self.vy *= 0.95

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Boundary checks (bounce)
        if self.x < 0:
            self.x = -self.x
            self.vx = -self.vx
        elif self.x > grid_size:
            self.x = 2 * grid_size - self.x
            self.vx = -self.vx
        
        if self.y < 0:
            self.y = -self.y
            self.vy = -self.vy
        elif self.y > grid_size:
            self.y = 2 * grid_size - self.y
            self.vy = -self.vy

class EpidemicSimulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.agents: List[Agent] = []
        self.stats = {"S": [], "E": [], "I": [], "R": [], "D": []}
        self.rt_history = [] # Track Rt over time
        self.init_agents()

    def init_agents(self):
        self.agents = []
        # Initial infected
        num_infected = 1
        for i in range(self.config.N):
            state = "S"
            timer = 0.0
            
            # Random position and velocity
            x = random.uniform(0, self.config.grid_size)
            y = random.uniform(0, self.config.grid_size)
            home_x = x
            home_y = y
            
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, 1)
            
            if i < num_infected:
                state = "I"
                # Sample infectious period
                timer = max(0, np.random.normal(self.config.infectious_mean, self.config.infectious_std))
            
            # Heterogeneity
            infectiousness = np.random.gamma(shape=2.0, scale=0.5) 
            susceptibility = random.uniform(0.5, 1.5)

            self.agents.append(Agent(
                id=i, x=x, y=y, vx=vx, vy=vy, 
                home_x=home_x, home_y=home_y,
                infectiousness=infectiousness, 
                susceptibility=susceptibility, 
                state=state,
                state_timer=timer
            ))
        
        self.update_stats()

    def step(self):
        # 1. Move agents
        for agent in self.agents:
            agent.move(self.config.grid_size, self.config.dt, self.config.home_attraction, self.config.random_force)

        # 2. Spatial Partitioning (Grid)
        grid_cell_size = max(self.config.interaction_radius, 1.0)
        grid: Dict[Tuple[int, int], List[Agent]] = {}
        
        for agent in self.agents:
            if agent.state == "D": 
                continue
            
            cx = int(agent.x / grid_cell_size)
            cy = int(agent.y / grid_cell_size)
            if (cx, cy) not in grid:
                grid[(cx, cy)] = []
            grid[(cx, cy)].append(agent)

        # 3. Determine Next States
        new_infections = 0
        current_infectious_agents = 0
        
        for agent in self.agents:
            agent.next_state = agent.state 
            agent.next_timer = agent.state_timer
            
            if agent.state == "D":
                continue
            
            # Decrement timer if in E or I
            if agent.state in ["E", "I"]:
                agent.next_timer -= self.config.dt

            # Infection Spread (S -> E)
            if agent.state == "S":
                # Vaccination (S -> R)
                if random.random() < self.config.vax_rate * self.config.dt:
                    agent.next_state = "R"
                else:
                    # Check neighbors
                    cx = int(agent.x / grid_cell_size)
                    cy = int(agent.y / grid_cell_size)
                    
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            ncx, ncy = cx + dx, cy + dy
                            if (ncx, ncy) in grid:
                                for neighbor in grid[(ncx, ncy)]:
                                    if neighbor.state == "I" and not neighbor.is_isolated:
                                        dist_sq = (agent.x - neighbor.x)**2 + (agent.y - neighbor.y)**2
                                        if dist_sq <= self.config.interaction_radius**2:
                                            # Probability
                                            prob = self.config.beta * neighbor.infectiousness * agent.susceptibility * self.config.dt
                                            if random.random() < prob:
                                                agent.next_state = "E"
                                                # Sample incubation period
                                                agent.next_timer = max(0, np.random.normal(self.config.incubation_mean, self.config.incubation_std))
                                                new_infections += 1
                                                break 
                        if agent.next_state == "E":
                            break

            # Transition E -> I
            elif agent.state == "E":
                if agent.next_timer <= 0:
                    agent.next_state = "I"
                    # Sample infectious period
                    agent.next_timer = max(0, np.random.normal(self.config.infectious_mean, self.config.infectious_std))
                    
                    # Intervention: Detection and Isolation
                    if random.random() < self.config.detection_prob:
                        if random.random() < self.config.isolation_compliance:
                            agent.is_isolated = True

            # Transition I -> R or D
            elif agent.state == "I":
                current_infectious_agents += 1
                if agent.next_timer <= 0:
                    if random.random() < self.config.mortality_rate:
                        agent.next_state = "D"
                    else:
                        agent.next_state = "R"
                    agent.is_isolated = False # No longer isolated (or doesn't matter)

        # 4. Apply Updates
        for agent in self.agents:
            if agent.state != agent.next_state:
                agent.state = agent.next_state
                agent.state_timer = agent.next_timer
                agent.days_in_state = 0
            else:
                agent.state_timer = agent.next_timer
                agent.days_in_state += self.config.dt

        self.update_stats(new_infections, current_infectious_agents)

    def update_stats(self, new_infections=0, current_infectious_agents=0):
        counts = {"S": 0, "E": 0, "I": 0, "R": 0, "D": 0}
        for agent in self.agents:
            counts[agent.state] += 1
        
        for key in counts:
            self.stats[key].append(counts[key])
            
        # Estimate Rt: New infections / (Current Infectious * dt * recovery_rate_approx)
        # This is instantaneous Rt. 
        # Simpler proxy: New Infections / dt / Current Infectious (if > 0) * Infectious Period
        if current_infectious_agents > 0:
            rt = (new_infections / self.config.dt) / current_infectious_agents * self.config.infectious_mean
        else:
            rt = 0.0
        self.rt_history.append(rt)

    def get_agent_data(self):
        return [{"id": a.id, "x": a.x, "y": a.y, "state": a.state, "days_in_state": a.days_in_state, "is_isolated": a.is_isolated} for a in self.agents]
