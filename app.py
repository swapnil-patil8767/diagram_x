from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq

app = Flask(__name__)
CORS(app)

# Set up your Groq API key
os.environ["GROQ_API_KEY"] = "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"

# Initialize the Groq LLM
groq = ChatGroq(
    model_name="groq/mixtral-8x7b-32768",
    temperature=0.7,
)

# Create customer support agent
# Agent 1: Mermaid Code Generator
mermaid_code_generator = Agent(
    role='Mermaid Diagram Creator',
    goal='Generate accurate and well-structured Mermaid code based on user input {input}',
    backstory="""An expert in creating visual diagrams using Mermaid.js syntax. 
    Proficient in interpreting user requirements and translating them into 
    appropriate Mermaid code for flowcharts, sequence diagrams, or other supported types.""",
    llm=groq
)

# Define task for Mermaid code generation
generate_mermaid_task = Task(
    description="""
    Create Mermaid.js code for diagrams based on user input by:
    1. Interpreting user requirements for the diagram type and structure
    2. Generating the corresponding Mermaid.js code
    3. Ensuring the code adheres to Mermaid.js syntax standards
    4. At time of generating a flowchart diagram do not write code for end state
    5.dont write additional code for colore

    Focus on:
    ER Diagrams 
    Flowcharts
    Sequence diagrams
    Class diagrams
    State diagrams
    """,
    expected_output="""
    A valid Mermaid.js code snippet that accurately represents the user-defined 
    diagram requirements. Code should be error-free and ready for rendering.
    only return a code .
    """,
    agent=mermaid_code_generator
)

# Agent 2: Mermaid Code Optimizer and Enhancer
mermaid_code_optimizer = Agent(
    role='Mermaid Code Enhancer',
    goal='Optimize and correct Mermaid code, adding enhancements based on user feedback',
    backstory="""A skilled developer with expertise in refining and optimizing Mermaid.js 
    code. Proficient in debugging syntax errors, enhancing visual clarity, and adding 
    additional elements as per user requests.""",
    llm=groq
)

# Define task for Mermaid code optimization
optimize_mermaid_task = Task(
    description="""
    Enhance, correct, or optimize Mermaid.js code by:
    1. Identifying syntax errors or logical flaws in the generated code
    2. Making improvements for better visual representation
    3. Adding additional elements as requested by the user
    4. Ensuring compatibility with Mermaid.js standards
    6. Remove any end state code from the diagram
    7 dont write additional code for colore
    Focus on:
    - Syntax corrections
    - Visual clarity
    - Adding requested enhancements
    """,
    expected_output="""
    A refined and optimized Mermaid.js code snippet that is error-free, visually 
    clear, and incorporates user-requested changes or additional elements.
    Do not return an explanation.
    """,
    agent=mermaid_code_optimizer
)

# Create and run the crew
crew = Crew(
    agents=[mermaid_code_generator, mermaid_code_optimizer],
    tasks=[generate_mermaid_task, optimize_mermaid_task]
)
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')
    
@app.route('/generate-mermaid', methods=['POST'])
def generate_mermaid():
    data = request.json
    description = data.get('description')

    if not description:
        return jsonify({'error': 'Description is required'}), 400

    input_data = {"input": description}
    result = crew.kickoff(inputs=input_data)
    result = str(result)

    def extract_mermaid_code(output):
        start_marker = "```mermaid"
        end_marker = "```"

        # Find the starting and ending indices
        start_index = output.find(start_marker)
        if start_index == -1:
            return "No mermaid block found."

        end_index = output.find(end_marker, start_index + len(start_marker))
        if end_index == -1:
            return "Incomplete mermaid block found."

        # Extract the code between the markers
        start_index += len(start_marker)
        mermaid_code = output[start_index:end_index].strip()
        return mermaid_code

    mermaid_code = extract_mermaid_code(result)
    return jsonify({'mermaidCode': mermaid_code})

port = int(os.environ.get("PORT", 10000))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port)
