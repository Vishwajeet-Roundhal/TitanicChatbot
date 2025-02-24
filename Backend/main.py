from fastapi import FastAPI, Query
import pandas as pd
import base64
import io
import matplotlib.pyplot as plt
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import re
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Load and preprocess Titanic dataset
df = pd.read_csv("titanic_data.csv")
df['Survived'] = df['Survived'].map({0: 'No', 1: 'Yes'})  # Convert to categorical

# Dataset metadata description
dataset_description = """
Titanic Dataset Columns:
- Survived: Survival (Yes/No)
- Pclass: Ticket class (1=1st, 2=2nd, 3=3rd)
- Sex: Gender
- Age: Age in years (378 missing values)
- SibSp: Siblings/spouses aboard
- Parch: Parents/children aboard
- Fare: Passenger fare
- Embarked: Port (C=Cherbourg, Q=Queenstown, S=Southampton)

Notable Statistics:
- Total passengers: 891
- Average age: 29.7 years
- Survival rate: 38.4%
- Common visualization options: distributions, survival comparisons, fare analysis
"""

# Enhanced prompt template
template = PromptTemplate.from_template(
    """You are a Titanic data analyst. Use this dataset context:
{metadata}

Respond following these rules:
1. For distribution questions, suggest HISTOGRAM:column_name
2. For comparisons, suggest BAR:group_column:value_column
3. For proportions, suggest PIE:column_name
4. For correlations, suggest SCATTER:x_column:y_column
5. Add visualization title after | symbol
6. Include text answer first

Question: {question}
Answer:"""
)

llm = Ollama(model="gemma")
chain = LLMChain(llm=llm, prompt=template)

@app.get("/")
def read_root():
    return {"message": "API working"}

@app.get("/query")
def query_titanic(question: str = Query(..., description="Ask any Titanic dataset question")):
    response = chain.invoke({"metadata": dataset_description, "question": question})
    answer_text = response["text"]
    
    viz_match = re.search(r"(HISTOGRAM|BAR|PIE|SCATTER):([^\|]+)\|(.+)", answer_text)
    visualization = None
    
    if viz_match:
        viz_type, columns, title = viz_match.groups()
        columns = [col.strip() for col in columns.split(",")] if "," in columns else columns
        answer_text = answer_text.replace(viz_match.group(0), "").strip()
        
        try:
            if viz_type == "HISTOGRAM":
                visualization = create_histogram(df, columns, title)
            elif viz_type == "BAR":
                group_col, value_col = columns.split(":")
                visualization = create_grouped_bar(group_col, value_col, title)
            elif viz_type == "PIE":
                visualization = create_pie_chart(df,columns, title)
            elif viz_type == "SCATTER":
                x_col, y_col = columns.split(":")
                visualization = create_scatter_plot(x_col, y_col, title)
        except Exception as e:
            logging.error(f"Visualization error: {str(e)}")
            answer_text += f"\n[Visualization error: {str(e)}]"

    return {
        "question": question,
        "answer": answer_text,
        "visualization": visualization
    }

def create_histogram(df, columns, title):
    if isinstance(columns, str):
        columns = [col.strip() for col in columns.split(",")]  # Ensure it's a list

    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        logging.warning(f"Columns missing: {missing_columns} (Available: {df.columns.tolist()})")
        return None

    plt.figure(figsize=(10, 6))
    for col in columns:
        df[col].dropna().hist(bins=20, alpha=0.5, label=col)

    plt.title(title)
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.legend(title="Columns")

    # Encode the plot
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()  # Prevent memory leaks
    buf.seek(0)

    return base64.b64encode(buf.read()).decode("utf-8")

def create_grouped_bar(group_col, value_col, title):
    
    group_col = group_col.strip()  # Remove any leading/trailing spaces
    value_col = value_col.strip()  

    plt.figure(figsize=(12, 6))
    
    # Handle multi-dimensional grouping
    if ":" in group_col:
        groups = group_col.split(":")
        df_group = df.groupby(groups)[value_col].value_counts(normalize=True).unstack() * 100
    else:
        df_group = df.groupby(group_col)[value_col].value_counts(normalize=True).unstack() * 100

    df_group.plot(kind='bar', stacked=False, color=['#ff9999','#66b3ff'])
    
    plt.title(title)
    plt.xlabel(" → ".join(groups) if ":" in group_col else group_col)
    plt.ylabel('Percentage (%)')
    plt.legend(title=value_col, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    
    return encode_plot()

def create_pie_chart(df, column, title):
    column = column.strip()  # Remove any leading/trailing spaces

    if column not in df.columns:
        logging.warning(f"Column '{column}' not found in DataFrame!")
        return None

    value_counts = df[column].value_counts()
    if len(value_counts) < 2:
        logging.warning(f"Column '{column}' does not have enough categories for a pie chart!")
        return None

    logging.info(f"Creating pie chart for column: {column}")
    
    plt.figure(figsize=(8, 8))
    value_counts.plot.pie(autopct='%1.1f%%', startangle=90, cmap="tab10")
    plt.title(title)
    plt.ylabel("")

    return encode_plot()


def create_scatter_plot(x_col, y_col, title):
    """
    Create and return a base64-encoded scatter plot image.

    Args:
        x_col (str): Column name for the x-axis.
        y_col (str): Column name for the y-axis.
        title (str): Title of the scatter plot.

    Returns:
        str: Base64-encoded image of the scatter plot.
    """
    x_col = x_col.strip()
    y_col = y_col.strip()
    # Check if columns exist in the DataFrame
    if x_col not in df.columns or y_col not in df.columns:
        logging.warning(f"Columns {x_col} or {y_col} are missing!")
        return None

    # Create scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.5, color='blue')
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)

    # Encode plot as base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    
    return base64.b64encode(buf.read()).decode("utf-8")

def encode_plot():
    """Helper to encode the current matplotlib figure as base64"""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')