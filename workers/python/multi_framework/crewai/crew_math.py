from crewai import Agent, Crew, Process, Task
from crewai.project import crew
from langchain_community.tools import tool
from dotenv import load_dotenv, find_dotenv
from crewai.tools import tool

# read local .env file 
# it should have MODEL (e.g. gpt-4o) and OPENAI_API_KEY
_ = load_dotenv(find_dotenv()) 

@tool("Add")
def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b

@tool("Multiply")
def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

@tool("Divide")
def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b

math_agent = Agent(
            role="Math Wizard",
            goal="use the calculator tool to do math",
            backstory="has done many calculations before"
        )

math_task=  Task(
            description="{prompt}",
            expected_output='Result of the mathematical expression',
            agent=math_agent,
            tools=[add, multiply, divide],  
        )

crew = Crew(
            agents=[math_agent],
            tasks=[math_task],
            process=Process.sequential,
            verbose=True,
)

class SimpleCalculatorCrew:
    @staticmethod
    def getCrew() -> Crew:
        return crew

# run the crew
if __name__ == "__main__":
    prompt = "sum 10 and 20"
    instance = SimpleCalculatorCrew().getCrew()
    result = instance.kickoff(inputs={'prompt': 'add 3 + 5 and divide the result by 2'})
    print(result)
