# team.py
class Team:
    def __init__(self, name, team_id=None, division_name=None, division_id=None):
        self.name = name
        self.team_id = team_id
        self.division_name = division_name
        self.division_id = division_id

    def update_team_data(self, team_id, division_name, division_id):
        self.team_id = team_id
        self.division_name = division_name
        self.division_id = division_id

    def __repr__(self):
        return f"Team(name={self.name}, team_id={self.team_id}, division_name={self.division_name}, division_id={self.division_id})"
