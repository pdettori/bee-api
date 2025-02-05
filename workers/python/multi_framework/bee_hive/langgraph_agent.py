
import importlib

from bee_hive.agent import Agent
from langchain_core.messages import HumanMessage, AIMessage

class LangGraphAgent(Agent):
    """
    LangGraphAgent extends the Agent class to load and run a specific LangGraph agent.
    """
    def __init__(self, agent: dict) -> str:
        """
        Initializes the workflow for the specified agent. 
        The executable code must be within $PYTHONPATH.
        Args:
            agent_name (dict): Agent Configuration
        Raises:
            Exception: If the agent cannot be loaded, an exception is raised with an error message.
        """

        super().__init__(agent)

        # TODO: Add additional properties later. for now using naming:
        #   <directory>.<filename>.<class>.<method> ie
        #   test.lg_test.MathAssistant.invoke

        try:
            partial_agent_name, method_name = self.agent_name.rsplit(".", 1)
            module_name, class_name = partial_agent_name.rsplit(".", 1)
            my_module = importlib.import_module(module_name)
            # Get the class object
            self.langgraph_agent_class = getattr(my_module, class_name)
            # Instantiate the class
            self.instance = self.langgraph_agent_class()            
            self.method_name = method_name
        except Exception as e:
            print(f"Failed to load agent {self.agent_name}: {e}")
            raise(e)


    def run(self, prompt: str) -> str:
        """
        Executes the LangGraph agent with the given prompt. The agent's `invoke` method is called with the input.
       
        Args:
            prompt (str): The input to be processed by the agent. 
        Returns:
            Any: The output from the agent's `invoke` method.
        Raises:
            Exception: If there is an error in retrieving or executing the agent's method.
        """
        print(f"Running LangGraph agent: {self.agent_name} with prompt: {prompt}")

        try:
            method = getattr(self.instance, self.method_name)
            messages = [HumanMessage(content=prompt)]
            response = method().invoke({"messages": messages})
            last_ai_message_content = None
            for message in response['messages']:
                if isinstance(message, AIMessage):
                    last_ai_message_content = message.content
            return last_ai_message_content       
        except Exception as e:
            print(f"Failed to kickoff langgraph agent: {self.agent_name}: {e}")
            raise(e)

    def run_streaming(self, prompt) ->str:
        """
        Streams the execution of the LangGraph agent with the given prompt.
        This is NOT YET IMPLEMENTED
        Args:
            prompt (str): The input prompt to be processed by the LangGraph agent.
        Raises:
            NotImplementedError: Indicates that the LangGraph agent execution logic is not yet implemented.
        """
        print(f"Running LangGraph agent (streaming): {self.agent_name} with prompt: {prompt}")

        raise NotImplementedError("LangGraph agent execution logic not implemented yet")
