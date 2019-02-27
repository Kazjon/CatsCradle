
from EmotionModule import EMOTION_DELTAS, try_add
import random

RULE_EXECUTION_PROBAS = {'tiny': 0.05, 'small': 0.2, 'medium': 0.4, 'large': 0.6}

class Responder(object):

    # static class variable
    all_rules = set()
    
    def __init__(self, action_module, response_module, p):
        self.p = p
        self.action_module = action_module
        self.response_module = response_module
        self.persons_to_look_list = []
        self.emotional_effect = {}
    

    def respond(self, emotion_module, audience, idle):
        raise NotImplementedError


    def execute_tracking(self):
        if len(self.persons_to_look_list) > 0:
            person_to_look_at = random.choice(self.persons_to_look_list)
            # unpacking
            person = person_to_look_at[0]
            look_function_str = person_to_look_at[1]
            look_duration = person_to_look_at[2]
            #if look_function_str == 'glance':
            #    self.response_module.glanceAt(person, duration=look_duration)
            #if look_function_str == 'look':
            #    self.response_module.lookAt(person, duration=look_duration)
            # reseting the list
            self.persons_to_look_list = []
    

    def execute_rule(self, audience, rule_str, filters_list, emotion_str, emotion_intensity, attention_str, attention_duration, proba):
        """
        Executes a rule.
        
        Args:
            audience (Audience).
            rule_str (str).
            filters_list (list).
            emotion_str (str).
            emotion_intensity (???).
            attention_str (str).
            attention_duration (float).
            proba (string). should be present in RULE_EXECUTION_PROBAS.keys()
        
        Returns:
            bool. If could execute the rule True otherwise False.
        """
        
        persons = []
        met_all_conditions = True
        for filter, quantity_condition in filters_list:
            filter_dict = dict(zip(['having_label', 'having_age', 'having_gender', 'recency'],
                                   filter))
            person_list = audience.get_people_with_condition(filter_dict)
            if len(person_list) > quantity_condition:
                persons.extend(person_list)
            else:
                met_all_conditions = False
                break
    
        # check the probability of execution
        if random.random() >= RULE_EXECUTION_PROBAS[proba]:
            return False
        
        if met_all_conditions:
            Responder.all_rules.add(rule_str)
            try_add(self.emotional_effect, emotion_str, emotion_intensity)
	    print(self.emotional_effect)
            if attention_str != "":
                for person in persons:
                    self.persons_to_look_list.append((person, attention_str, attention_duration))
            return True
        else:
            return False
    
    
    def execute_rules(self, audience, rules_list):
        """
        Execute list of rules.
        """

        for rule in rules_list:
            # unpack the rule
            rule_str = rule[0]
            filters_list = rule[1]
            emotion_str = rule[2]
            emotion_intensity = EMOTION_DELTAS[rule[3]]
            attention_str = rule[4]
            attention_duration = rule[5]
            proba = rule[6]
            
            if self.execute_rule(audience, rule_str, filters_list, emotion_str, emotion_intensity, attention_str, attention_duration, proba):
                break

