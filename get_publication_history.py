import db_info

class GetPublicationHistory:

    def __init__(self, user='root', password='password', verbose=False,
                 table='profs_list_unique'):
        self.table = table
        self.user = user
        self.password = password
        self.verbose = verbose
        self.pct_found = None

    def get_history(self):
        return None
