import random
import numpy as np
import pandas as pd
import itertools
import copy
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, 
                                                  # next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.gamma = 0.1 #discount rate; arbitrarily selected this value
        self.alpha = 0.8 #learning rate; arbitrarily selected this value
    
        #CREATE STARTING Q LEARNING MATRIX
        print "Setting up Q learning matrix and tracking variables..."          
        #Set variables/lists determining the Q matrix' size
        actions = self.env.valid_actions
        lights = ['green', 'red']
        
        #create Q matrix
        #states/rows use this coding system [next_waypoint, light_status, oncoming, left, right]
        row_names = np.empty(0)       
        for combination in itertools.product(actions, lights, actions, actions, actions):  #time_list
            row_name = '*'.join(map(str, list(combination)))          
            row_names = np.append(row_names,row_name)
       
        #initialize Q matrix to have argmax actions equal to planner supplied actions
        col_labels = copy.deepcopy(actions)
        col_labels[0] = str(col_labels[0])
        self.Q = pd.DataFrame(0, index=row_names, columns=col_labels)        
        for row in list(self.Q.index):
            recommended_action = row.split("*")[0]
            self.Q.loc[row, recommended_action] = 3.5
            
        #Initialize variables to keep track of previous state, action and reward
        self.state = None
        self.prev_state = None
        self.prev_action = None
        self.prev_reward = None
        self.net_reward = 0
        
        print "DONE; start learning..."

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required

    def update(self, t):
             
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        deadline = self.env.get_deadline(self) #Current dealine remaining (in time steps)        
        inputs = self.env.sense(self)  #Need to determine traffic light status, presence of cars
        light = inputs['light']
        oncoming = inputs['oncoming']
        left = inputs['left']
        right = inputs['right']        
        #state = self.env.agent_states[self]             
        
        # TODO: Update state
        #states use this coding system [next_waypoint, light_status, oncoming, left, right]       
        current_state = '*'.join(map(str, list((self.next_waypoint, light, oncoming, 
                                               left, right)))) #time left to reach desination
        self.state = current_state
        
        # TODO: Learn policy based on state, action, reward
        #Update Q matrix now that we know the future state (s')
        #current_state is equal to future state (s') from previous iteration
        if (self.prev_state != None):  
            max_Qprime = max (self.Q.loc[current_state, ]) #Utility of next state (s')
            #Utility of state (s) = Q(s,a) = R(s,a) + gamma * max,a' [Q(s',a')]            
            utility = self.prev_reward + self.gamma * max_Qprime
            #Learning rate update formula: V <-- (1 - alpha) * V + alpha * X            
            s = str(self.prev_state)            
            a = str(self.prev_action)
            self.Q.loc[s, a] = (1 - self.alpha) * self.Q.loc[s, a] + self.alpha * (utility)        
                    
        # TODO: Select action according to your policy
        # Part I of assignment tells me to randomly select an action        
        #action = random.choice(self.env.valid_actions)
        
        # Part II of the assignment telss me to pick the action with the highest Q value in that state        
        action = self.Q.loc[current_state, ].idxmax(axis=0)
        if action == "None":
            action = None
        
        self.prev_action = action #Remember your previous action (a)

        # Execute action and get reward
        reward = self.env.act(self, action)
        self.net_reward += reward
        self.prev_state = current_state  #Remember what state you came from (s)
        self.prev_reward = reward #This is to remember the R(s,a) value for calculating Q(s,a)
                                  #Can't do Q(s,a) update until future state (s') is known

        print "LearningAgent.update(): deadline = {}, current_state = {}, action = {}, reward = {}, net_reward = {}".format(deadline, 
                                         self.state, action, reward, self.net_reward)  # [debug]
        
    #My implementation didn't use this Udacity given function
    #def get_future_state(self, t):
        #print "Environment.step(): t = {}".format(self.t)  # [debug]

        # Update traffic lights
    #    for intersection, traffic_light in self.env.intersections.iteritems():
    #        traffic_light.update(self.t)

        # Update agents
    #    for agent in self.agent_states.iterkeys():
    #        agent.update(self.t)

    #    if self.primary_agent is not None:
    #        if self.enforce_deadline and self.agent_states[self.primary_agent]['deadline'] <= 0:
    #            self.done = True
    #            print "Environment.reset(): Primary agent could not reach destination within deadline!"
    #        self.agent_states[self.primary_agent]['deadline'] -= 1


def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=False)  # set agent to track

    # Now simulate it
    sim = Simulator(e, update_delay=0.01)  # reduce update_delay to speed up simulation
    sim.run(n_trials=100)  # press Esc or close pygame window to quit


if __name__ == '__main__':
    run()
