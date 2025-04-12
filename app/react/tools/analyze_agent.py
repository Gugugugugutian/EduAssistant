from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from dataclasses import dataclass

import os
import pandas as pd
import peewee
from flask import session
from playhouse.shortcuts import model_to_dict

from app.models.learning_data import *
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment, StudentAssignment
from app.react.tools_register import register_as_tool

def data_frame_from_peewee_query(query: peewee.Query) -> pd.DataFrame:
    connection = query._database.connection()  # noqa
    sql, params = query.sql()
    return pd.read_sql_query(sql, connection, params=params)

def flatten_dict(data):
    """Flatten a dictionary of dictionaries into a single dictionary"""
    df = pd.json_normalize(data, sep='_')
    d_flat = df.to_dict(orient='records')[0]
    return d_flat

    

df = None

@dataclass
class Deps:
    """The only dependency we need is the DataFrame we'll be working with."""
    df: pd.DataFrame

model = OpenAIModel(
    'deepseek-chat',
    provider=DeepSeekProvider(api_key=os.getenv('DEEPSEEK_API_KEY')),
)

agent = Agent(
    model=model,
    system_prompt="""You are an AI assistant that helps extract information from a pandas DataFrame.
    If asked about columns, be sure to check the column names first.
    Be concise in your answers.""",
    deps_type=Deps,

    # Allow the agent to make mistakes and correct itself. Details will be covered in the tool definition.
    retries=10,
)


@agent.tool
async def df_query(ctx: RunContext[Deps], query: str) -> str:
    """A tool for running queries on the `pandas.DataFrame`. Use this tool to interact with the DataFrame.

    `query` will be executed using `pd.eval(query, target=df)`, so it must contain syntax compatible with
    `pandas.eval`.

    If column names were not provided, get by "df.columns".

    Example query: df.['some_column'].mean()
    
    """

    # Print the query for debugging purposes and fun :)
    print(f'Running query: `{query}`')
    try:
        # Execute the query using `pd.eval` and return the result as a string (must be serializable).
        print("Query result:", str(pd.eval(query, target=ctx.deps.df)))
        return str(pd.eval(query, target=ctx.deps.df))
    except Exception as e:
        #  On error, raise a `ModelRetry` exception with feedback for the agent.
        print("Query error:", e)
        raise ModelRetry(f'query: `{query}` is not a valid query. Reason: `{e}`') from e


def ask_agent(question, df):
    """Function to ask questions to the agent and display the response"""
    deps = Deps(df=df)
    print(f"Question: {question}")
    result = agent.run_sync(question, deps=deps)
    #print(f"Answer: {response.new_messages()[-1].content}")
    print(f"Answer: {result.data}")
    print("---")
    return result.data


@register_as_tool(['teacher', 'student'])
def learning_analyze(question, df_to_be_analyzed):
    '''Ask the analyzing agent to generate a analysis report based on the question and selected dataframe.

    If you are prompted to do analytical tasks, PRIORITIZE USING THIS TOOL instead of do it yourself.
    Message history hasn't been implemented yet. So you may not ask the agent to do further analysis based on previous results.

    Args:
        question (str): self-explanatory
        df_to_be_analyzed (str): 
            The dataframe you want to analyze. If the user is a student, only her/his data are provided. If the user is a teacher, only the students enrolled in her/his courses are involved.
            options: "knowledge_mastery", "learning_activity", "assignment"

    Returns:
        str: Analysis results
    '''
    Student = User.alias()
    Teacher = User.alias()
    if df_to_be_analyzed == "knowledge_mastery":
        base_query = (
            StudentKnowledgePoint
            .select(Student.name.alias("student_name"), Student.id.alias("student_id"),
                    KnowledgePoint.name.alias("knowledge_point_name"), KnowledgePoint.id.alias("knowledge_point_id"),
                    StudentKnowledgePoint.mastery_level,
                    Course.name.alias("course_name"), Course.code.alias("course_code"), Course.id.alias("course_id"),
                    Teacher.name.alias("teacher_name"), Teacher.id.alias("teacher_id"))
            .join(Student)
            .switch(StudentKnowledgePoint)
            .join(KnowledgePoint)
            .join(Course)
            .join(Teacher)
        )
        description = "df is about the knowledge point mastery levels of students."
    elif df_to_be_analyzed == "learning_activity":
        base_query = (
            LearningActivity
            .select(Student.name.alias("student_name"), Student.id.alias("student_id"),
                    Course.name.alias("course_name"), Course.code.alias("course_code"), Course.id.alias("course_id"),
                    LearningActivity.activity_type, LearningActivity.duration, LearningActivity.timestamp,
                    Teacher.name.alias("teacher_name"), Teacher.id.alias("teacher_id"))
            .join(Student)
            .switch(LearningActivity)
            .join(Course)
            .join(Teacher)
        )
        description = "df is about the learning activities of students."
    elif df_to_be_analyzed == "assignment":
        base_query = (
            StudentAssignment
            .select(Student.name.alias("student_name"), Student.id.alias("student_id"),
                    Course.name.alias("course_name"), Course.code.alias("course_code"), Course.id.alias("course_id"),
                    Assignment.title.alias("assignment_title"), Assignment.id.alias("assignment_id"),
                    StudentAssignment.score, StudentAssignment.submitted_at, StudentAssignment.attempts,
                    Assignment.total_points,
                    Teacher.name.alias("teacher_name"), Teacher.id.alias("teacher_id"))
            .join(Student)
            .switch(StudentAssignment)
            .join(Assignment)
            .join(Course)
            .join(Teacher)
        )
        description = "df is about the assignments of students."
    
    user = User.get_by_id(session['user_id'])
    if user.roles[0].role.name == 'teacher':
        query = base_query.where(Teacher.id==user.id)
    elif user.roles[0].role.name == 'student':
        query = base_query.where(Student.id==user.id)

    print(f"User {user.name}(id: {user.id}) querying the analysis agent.")

    global df
    df = data_frame_from_peewee_query(query)

    return ask_agent(
        question=description+'\n'+f"dataframe columns:{df.columns}\n"+question,
        df=df
    )


def test():
    #ask_agent("")
    from app import create_app
    create_app()
    #global df
    '''df = data_frame_from_peewee_query(
        StudentKnowledgePoint
        .select(User.name.alias("student_name"), User.id.alias("student_id"),
                KnowledgePoint.name.alias("knowledge_point_name"), KnowledgePoint.id.alias("knowledge_point_id"),
                StudentKnowledgePoint.mastery_level)
        .join(User)
        .switch(StudentKnowledgePoint)
        .join(KnowledgePoint)
        )'''
    '''df = pd.DataFrame(
        [flatten_dict(model_to_dict(skp, max_depth=2)) for skp in StudentKnowledgePoint.select()]
    )'''
    #print(df.columns)
    #ask_agent("Please summarize the knowledge mastery level of student Chen Jie.", df)
    #print("="*50)
    #print(learning_analyze("Please give a comprehensive report about the knowledge point mastery levels of students in my class 'CS101'.", "knowledge_mastery"))
    print("="*50)
    print(learning_analyze("Please give a comprehensive report about the learning activities of students in my class 'CS101'(course code).", "learning_activity"))
    print("="*50)
    print(learning_analyze("Please give a comprehensive report about the learning situations of students in my class 'CS101(course code)' according to the assignment scores.", "assignment"))
    

if __name__ == '__main__':
    session = {}
    session['user_id'] = 2
    test()