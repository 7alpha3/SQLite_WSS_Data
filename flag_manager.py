# FlagManager class to encapsulate boolean flag value held in a mutable list
class FlagManager:
    def __init__(self):
        self.flag = [False]

    def set_flag(self):
        self.flag[0] = True

    def clear_flag(self):
        self.flag[0] = False

    def is_set(self):
        return self.flag[0]
    
    def is_cleared(self):
        return not self.flag[0]

    def __del__(self):
        pass