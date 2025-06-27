#!/usr/bin/env python3
"""
SQL Agent Evaluation Script

This script provides comprehensive evaluation capabilities for the Multi-Tenant SQL Agent
using LangSmith's evaluation framework. It includes:

1. Dataset creation and management
2. Automated evaluation runs
3. Custom evaluators for SQL agent performance
4. Performance metrics and reporting

Usage:
    python evaluate_agent.py
"""

import uuid
import os
from datetime import datetime
from typing import Dict, List, Any

from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith.schemas import Example, Run

from multitenant_api import create_multitenant_sql_agent
from settings import settings


class SQLAgentEvaluator:
    """Comprehensive evaluation framework for the Multi-Tenant SQL Agent."""
    
    def __init__(self, test_database_name: str = "test_evaluation_db"):
        """Initialize the evaluator with LangSmith client and agent."""
        self.client = Client()
        self.test_database_name = test_database_name
        self.agent = create_multitenant_sql_agent(test_database_name)
        self.project_name = settings.langchain_project or "Multi-Tenant SQL Agent"
        
    def create_evaluation_dataset(self, dataset_name: str, questions: List[Dict[str, Any]]) -> str:
        """
        Create or update an evaluation dataset in LangSmith.
        
        Args:
            dataset_name: Name of the dataset
            questions: List of question dictionaries with 'input' and optionally 'expected_output'
            
        Returns:
            Dataset ID
        """
        try:
            # Check if dataset already exists
            dataset = self.client.read_dataset(dataset_name=dataset_name)
            print(f"✅ Dataset '{dataset_name}' already exists with {len(list(self.client.list_examples(dataset_id=dataset.id)))} examples")
            return dataset.id
        except Exception:
            # Create new dataset
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=f"Evaluation questions for {self.project_name}"
            )
            
            # Add examples to the dataset
            for q in questions:
                self.client.create_example(
                    inputs={"input": q["input"]},
                    outputs=q.get("expected_output"),
                    dataset_id=dataset.id
                )
            
            print(f"✅ Created dataset '{dataset_name}' with {len(questions)} examples")
            return dataset.id
    
    def agent_target(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Target function for evaluation - runs the agent on a single example.
        
        Args:
            example: Input example from the dataset
            
        Returns:
            Agent response with output and intermediate steps
        """
        session_id = f"eval_session_{uuid.uuid4().hex[:8]}"
        
        try:
            response = self.agent.invoke(
                {"input": example["input"]},
                config={"configurable": {"session_id": session_id}}
            )
            
            return {
                "output": response.get("output", ""),
                "intermediate_steps": response.get("intermediate_steps", []),
                "success": True
            }
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e)
            }
    
    def create_custom_evaluators(self) -> List[Any]:
        """Create custom evaluators for SQL agent performance."""
        
        # 1. Response Quality Evaluator
        response_quality_evaluator = LangChainStringEvaluator(
            "labeled_score_string",
            config={
                "criteria": {
                    "accuracy": "Is the response factually correct based on the database query results?",
                    "completeness": "Does the response fully answer the user's question?",
                    "clarity": "Is the response clear and easy to understand?"
                },
                "normalize_by": 3  # Average of the 3 criteria
            }
        )
        
        # 2. SQL Query Evaluator
        def sql_query_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate the quality of generated SQL queries."""
            output = run.outputs.get("output", "")
            intermediate_steps = run.outputs.get("intermediate_steps", [])
            
            # Extract SQL queries from intermediate steps
            sql_queries = []
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) > 1:
                    action = step[0]
                    if hasattr(action, 'tool_input') and 'query' in str(action.tool_input):
                        sql_queries.append(str(action.tool_input))
            
            score = 0
            feedback = []
            
            # Check if SQL was generated
            if sql_queries:
                score += 0.5
                feedback.append("✅ SQL query generated")
                
                # Check for common SQL best practices
                sql_text = " ".join(sql_queries).upper()
                if "LIMIT" in sql_text:
                    score += 0.2
                    feedback.append("✅ Uses LIMIT clause")
                if "ORDER BY" in sql_text:
                    score += 0.1
                    feedback.append("✅ Uses ORDER BY")
                if "WHERE" in sql_text:
                    score += 0.1
                    feedback.append("✅ Uses WHERE clause")
                if "JOIN" in sql_text:
                    score += 0.1
                    feedback.append("✅ Uses JOIN")
            else:
                feedback.append("❌ No SQL query generated")
            
            return {
                "key": "sql_quality",
                "score": min(score, 1.0),
                "value": score,
                "comment": "; ".join(feedback)
            }
        
        # 3. Error Handling Evaluator
        def error_handling_evaluator(run: Run, example: Example) -> Dict[str, Any]:
            """Evaluate how well the agent handles errors."""
            success = run.outputs.get("success", True)
            error = run.outputs.get("error")
            
            if success:
                return {
                    "key": "error_handling",
                    "score": 1.0,
                    "value": 1.0,
                    "comment": "✅ No errors encountered"
                }
            else:
                # Check if error was handled gracefully
                output = run.outputs.get("output", "")
                if "Error:" in output and len(output) > 10:
                    return {
                        "key": "error_handling",
                        "score": 0.5,
                        "value": 0.5,
                        "comment": f"⚠️ Error handled gracefully: {error}"
                    }
                else:
                    return {
                        "key": "error_handling",
                        "score": 0.0,
                        "value": 0.0,
                        "comment": f"❌ Error not handled well: {error}"
                    }
        
        return [response_quality_evaluator, sql_query_evaluator, error_handling_evaluator]
    
    def run_evaluation(self, dataset_name: str, experiment_name: str = None) -> Dict[str, Any]:
        """
        Run a comprehensive evaluation of the SQL agent.
        
        Args:
            dataset_name: Name of the dataset to evaluate on
            experiment_name: Optional custom experiment name
            
        Returns:
            Evaluation results
        """
        if not experiment_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_name = f"SQL_Agent_Eval_{timestamp}"
        
        print(f"🚀 Starting evaluation: {experiment_name}")
        print(f"📊 Dataset: {dataset_name}")
        print(f"🤖 Agent: {self.project_name}")
        
        # Get custom evaluators
        evaluators = self.create_custom_evaluators()
        
        # Run evaluation
        results = evaluate(
            self.agent_target,
            data=dataset_name,
            evaluators=evaluators,
            experiment_prefix=experiment_name,
            description=f"Comprehensive evaluation of {self.project_name}",
            max_concurrency=1  # Run sequentially to avoid database connection issues
        )
        
        print(f"✅ Evaluation complete!")
        print(f"📈 View results in LangSmith: {self.client.api_url}/projects/{self.project_name}")
        
        return results


def get_sample_questions() -> List[Dict[str, Any]]:
    """Get sample evaluation questions for the SQL agent."""
    return [
        {
            "input": "How many records are in the database?",
            "expected_output": None  # Will be filled based on actual data
        },
        {
            "input": "What tables are available in this database?",
            "expected_output": None
        },
        {
            "input": "Show me the first 5 rows from the largest table",
            "expected_output": None
        },
        {
            "input": "What are the column names and types for each table?",
            "expected_output": None
        },
        {
            "input": "Find any tables that might contain user or customer information",
            "expected_output": None
        },
        {
            "input": "What's the total count of rows across all tables?",
            "expected_output": None
        },
        {
            "input": "Show me some sample data from different tables",
            "expected_output": None
        },
        {
            "input": "Are there any relationships between tables?",
            "expected_output": None
        },
        {
            "input": "What's the date range of data in this database?",
            "expected_output": None
        },
        {
            "input": "Find tables with the most recent data",
            "expected_output": None
        }
    ]


def main():
    """Main evaluation script."""
    print("🔍 SQL Agent Evaluation Framework")
    print("=" * 50)
    
    # Initialize evaluator
    evaluator = SQLAgentEvaluator()
    
    # Check if agent is properly initialized
    if not evaluator.agent:
        print("❌ Agent not properly initialized. Please check your configuration.")
        return
    
    print(f"✅ Agent initialized for database: {evaluator.test_database_name}")
    
    # Create evaluation dataset
    dataset_name = "SQL_Agent_Comprehensive_Eval"
    questions = get_sample_questions()
    
    dataset_id = evaluator.create_evaluation_dataset(dataset_name, questions)
    
    # Run evaluation
    print("\n" + "=" * 50)
    results = evaluator.run_evaluation(dataset_name)
    
    print("\n" + "=" * 50)
    print("📊 Evaluation Summary:")
    print(f"   • Dataset: {dataset_name}")
    print(f"   • Questions evaluated: {len(questions)}")
    print(f"   • Project: {evaluator.project_name}")
    print(f"   • View detailed results in LangSmith dashboard")


if __name__ == "__main__":
    main()
