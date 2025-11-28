import unittest
import numpy as np
from simulation import EpidemicSimulation, SimulationConfig

class TestEpidemicSimulation(unittest.TestCase):
    def setUp(self):
        self.config = SimulationConfig(
            N=100,
            grid_size=50.0,
            beta=1.0,
            incubation_mean=5.0,
            incubation_std=0.0, # Deterministic for testing
            infectious_mean=7.0,
            infectious_std=0.0, # Deterministic for testing
            mortality_rate=0.0,
            vax_rate=0.0,
            dt=1.0,
            home_attraction=0.0,
            random_force=0.0
        )
        self.sim = EpidemicSimulation(self.config)

    def test_population_conservation(self):
        self.sim.step()
        total_agents = sum(len(self.sim.stats[state]) for state in ["S", "E", "I", "R", "D"])
        # Stats are lists of counts, so we check the last element
        current_total = (
            self.sim.stats["S"][-1] +
            self.sim.stats["E"][-1] +
            self.sim.stats["I"][-1] +
            self.sim.stats["R"][-1] +
            self.sim.stats["D"][-1]
        )
        self.assertEqual(current_total, self.config.N)

    def test_initial_infection(self):
        # Should have 1 infected initially
        infected_count = sum(1 for a in self.sim.agents if a.state == "I")
        self.assertEqual(infected_count, 1)

    def test_state_transitions_timer(self):
        # Test E -> I transition
        agent = self.sim.agents[0]
        agent.state = "E"
        agent.state_timer = 2.0 # 2 days left
        agent.next_state = "E"
        
        # Step 1: Timer becomes 1.0
        self.sim.step()
        # Find the agent (id 0)
        agent = next(a for a in self.sim.agents if a.id == 0)
        self.assertEqual(agent.state, "E")
        self.assertAlmostEqual(agent.state_timer, 1.0)
        
        # Step 2: Timer becomes 0.0 -> Transition to I
        self.sim.step()
        agent = next(a for a in self.sim.agents if a.id == 0)
        self.assertEqual(agent.state, "I")
        # Should have new timer (infectious period)
        self.assertAlmostEqual(agent.state_timer, 7.0)

    def test_isolation(self):
        # Enable isolation
        self.sim.config.detection_prob = 1.0
        self.sim.config.isolation_compliance = 1.0
        
        agent = self.sim.agents[0]
        agent.state = "E"
        agent.state_timer = 1.0 # Will transition next step
        
        self.sim.step()
        
        agent = next(a for a in self.sim.agents if a.id == 0)
        self.assertEqual(agent.state, "I")
        self.assertTrue(agent.is_isolated)
        
        # Verify isolated agent doesn't move (vx, vy should be ignored or 0)
        # In our logic, move() returns early if isolated.
        # Let's set velocity and check position.
        agent.vx = 10.0
        agent.x = 10.0
        
        self.sim.step()
        
        agent = next(a for a in self.sim.agents if a.id == 0)
        self.assertEqual(agent.x, 10.0) # Should not have moved

if __name__ == '__main__':
    unittest.main()
