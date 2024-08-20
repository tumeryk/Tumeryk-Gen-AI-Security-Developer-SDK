class UserData:
    """Class to store data associated with each user."""

    def __init__(self):
        self.chat_log = []
        self.chat_responses = []
        self.guard = []
        self.guard_log = []
        self.guard_log_response = []
        self.models = {}  # Cache for storing LLM models keyed by config_id
        self.configs = []
        self.config_id = ""
        self.llm_chain_cache = {}  # Cache for LLMChains
        self.api_key_cache = {}  # Cache for API keys


db_dict = {}


def get_user_data(username: str) -> UserData:
    """Retrieve or create the UserData for the specified user."""
    if username not in db_dict:
        db_dict[username] = UserData()
    return db_dict[username]
