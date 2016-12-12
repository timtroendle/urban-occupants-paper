class Person():

    def __init__(self, activity_markov_chain, initial_activity, number_generator):
        self.__chain = activity_markov_chain
        self.activity = initial_activity
        self.__number_generator = number_generator

    def step(self):
        self.activity = self.__chain.move(state=self.activity, random_func=self.__number_generator)
