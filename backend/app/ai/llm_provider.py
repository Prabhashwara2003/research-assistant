from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic

class LLMProvider :
    
    def __init__(
        self,
        api_key : str,
        model_name : str
    ):
        self.api_key = api_key
        self.model_name = model_name
        
    def create_model(self)->BaseChatModel:
        
        model = ChatAnthropic(
            model = self.model_name,
            api_key=self.api_key
        )
        
        return model
        
