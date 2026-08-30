class PlayerService:
    def __init__(self, repository):
        self.repository = repository

    def get_player(self, name):
        return self.repository.find_player_by_name(name)

    def create_player(self, name):
        return self.repository.create_player(name)

    def get_ranking(self):
        return self.repository.get_ranking()

    def add_score(self, name, points):
        return self.repository.add_score(
            name,
            points
        )

    def delete_player(self, name):
        return self.repository.delete_player(name)

    def transfer_score(
            self,
            sender,
            receiver,
            points
    ):
        return self.repository.transfer_score(
            sender,
            receiver,
            points
        )

    def get_transfer_history(
            self,
            limit=20,
            offset=0
    ):
        return self.repository.get_transfer_history(
            limit=limit,
            offset=offset
        )