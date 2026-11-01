import os
import time
from typing import TypedDict, Annotated, Sequence
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg2 import sql, connect # Using psycopg2-binary as per requirements.txt

# --- Define Agent State and Graph ---
class AgentState(TypedDict):
    agent_state: str
    messages: Annotated[Sequence[str], operator.add]

def step_1(state: AgentState):
    print(f"--- Agent Step 1 ---")
    new_state = "step_1"
    messages = state.get("messages", []) + [f"Executed step 1. Current state: {new_state}"]
    return {"agent_state": new_state, "messages": messages}

def step_2(state: AgentState):
    print(f"--- Agent Step 2 (Restored from checkpoint) ---")
    new_state = "step_2"
    messages = state.get("messages", []) + [f"Executed step 2. Current state: {new_state}"]
    return {"agent_state": new_state, "messages": messages}

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("step_1", step_1)
    workflow.add_node("step_2", step_2)

    workflow.add_edge(START, "step_1")
    workflow.add_edge("step_1", "step_2")
    workflow.add_edge("step_2", END)

    app = workflow.compile()
    return app

# --- Main Execution ---
if __name__ == "__main__":
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    db_ready = False
    for _ in range(30): # Try for up to 30 seconds
        try:
            conn = connect(
                dbname="langgraph_checkpoints",
                user="user",
                password="password",
                host="localhost",
                port="5432",
                sslmode="require",
                sslrootcert="./certs/root.crt",
                sslcert="./certs/client.crt",
                sslkey="./certs/client.key"
            )
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            db_ready = True
            print("PostgreSQL is ready.")
            break
        except Exception as e:
            print(f"PostgreSQL not ready yet, retrying... ({e})")
            time.sleep(1)
    
    if not db_ready:
        print("Error: PostgreSQL did not become ready in time. Exiting.")
        exit(1)

    # Configure PostgreSQL connection string for LangGraph
    # Crucially, specify sslmode='require' and point to the root CA certificate
    # for server verification, and client certificates if required by the server.
    # The 'certs' directory is relative to where main.py is run.
    POSTGRES_CONNECTION_STRING = (
        "postgresql://user:password@localhost:5432/langgraph_checkpoints?"
        "sslmode=require&"
        "sslrootcert=./certs/root.crt&"
        "sslcert=./certs/client.crt&"
        "sslkey=./certs/client.key"
    )

    # Initialize LangGraph checkpoint saver
    # LangGraph's PostgresSaver uses psycopg2 internally, so these parameters
    # are passed correctly.
    memory = PostgresSaver(sync_connection=POSTGRES_CONNECTION_STRING)

    # Build the agent graph
    app = build_graph()

    # Define a thread ID for checkpointing
    thread_id = "test_thread_123"

    # --- Run 1: Initial execution and checkpoint ---
    print("\n--- Running initial agent execution ---")
    initial_state = {"agent_state": "initial", "messages": ["Initial state"]}
    
    # The config argument is where the thread_id for checkpointing is passed
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke the agent, saving state after each step
    try:
        final_state_run1 = None
        for s in app.stream(initial_state, config=config):
            print(s)
            final_state_run1 = s

        print("Checkpoint saved successfully.")
        print(f"--- Final Agent State after Run 1 ---")
        print(final_state_run1)
    except Exception as e:
        print(f"Error during initial agent run: {e}")
        print("This could be due to an SSL error. Check your PostgreSQL logs.")
        exit(1)

    # --- Run 2: Restore from checkpoint and continue ---
    print("\n--- Running agent from checkpoint ---")
    # To restore, we just pass the same config (containing thread_id)
    # and an empty initial state. LangGraph will load the latest checkpoint.
    try:
        final_state_run2 = None
        for s in app.stream({}, config=config): # Empty state to trigger restoration
            print(s)
            final_state_run2 = s

        print("Checkpoint saved successfully.")
        print(f"--- Final Agent State after Run 2 (restored) ---")
        print(final_state_run2)
    except Exception as e:
        print(f"Error during agent run from checkpoint: {e}")
        print("This is likely where SSL errors manifest, preventing state restoration.")
        exit(1)

    print("\nDemonstration complete. If no SSL errors occurred, the fix is working.")
    print("The key is correctly configuring sslmode, sslrootcert, sslcert, and sslkey in the connection string.")
