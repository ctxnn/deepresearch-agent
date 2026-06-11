
"""Research Utilities and Tools.

This module provides search and content processing utilities for the research agent,
including web search capabilities and content summarization tools.
"""

from pathlib import Path
from datetime import datetime
import re
import json
import uuid
import time
import asyncio
from typing_extensions import Annotated, List, Literal

from langchain.chat_models import init_chat_model 
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from tavily import TavilyClient

from reisearch.state_research import Summary
from reisearch.prompts import summarize_webpage_prompt

# ===== UTILITY FUNCTIONS =====

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")

def get_current_dir() -> Path:
    """Get the current directory of the module.

    This function is compatible with Jupyter notebooks and regular Python scripts.

    Returns:
        Path object representing the current directory
    """
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ is not defined
        return Path.cwd()

def invoke_safe_structured_output(model, schema, messages, max_retries=3, delay=2.0):
    """Safely invoke a model with structured output, recovering from Groq's parser failures if possible."""
    structured_model = model.with_structured_output(schema)
    last_err = None
    for attempt in range(max_retries):
        try:
            return structured_model.invoke(messages)
        except Exception as e:
            last_err = e
            body = getattr(e, "body", None)
            if body and isinstance(body, dict):
                error_info = body.get("error", {})
                failed_generation = error_info.get("failed_generation", "")
                if failed_generation:
                    failed_generation = failed_generation.strip()
                    params = None
                    
                    # Try parsing as JSON array/object directly
                    try:
                        data = json.loads(failed_generation)
                        if isinstance(data, list) and len(data) > 0:
                            first_call = data[0]
                            if isinstance(first_call, dict):
                                params = first_call.get("parameters") or first_call.get("args") or first_call
                            else:
                                params = first_call
                        elif isinstance(data, dict):
                            params = data.get("parameters") or data.get("args") or data
                    except Exception:
                        pass
                    
                    # Fallback to regex and block extraction
                    if not params:
                        # 1. Try to find standard tool call XML tag
                        match = re.search(r'<function=[^>]+>(.*?)(?:</function>|$)', failed_generation, re.DOTALL)
                        json_str = None
                        if match:
                            json_str = match.group(1).strip()
                        else:
                            # 2. Try to find markdown JSON block
                            match_code_block = re.search(r'```(?:json)?\s*(.*?)\s*```', failed_generation, re.DOTALL)
                            if match_code_block:
                                json_str = match_code_block.group(1).strip()
                            else:
                                # 3. Extract between first '{' and last '}'
                                start_idx = failed_generation.find('{')
                                end_idx = failed_generation.rfind('}')
                                if start_idx != -1 and end_idx != -1:
                                    json_str = failed_generation[start_idx:end_idx+1].strip()
                        
                        if json_str:
                            json_str = json_str.replace("\\'", "'")
                            try:
                                params = json.loads(json_str, strict=False)
                            except Exception:
                                pass
                    
                    if isinstance(params, dict):
                        # Fuzzy key matching: map model-produced keys to actual schema keys
                        schema_keys = list(schema.model_fields.keys())
                        for sk in schema_keys:
                            if sk not in params:
                                for pk in list(params.keys()):
                                    if pk not in schema_keys:
                                        if sk == 'summary' and any(x in pk.lower() for x in ['summary', 'sum', 'abstract']):
                                            params[sk] = params.pop(pk)
                                            break
                                        elif sk == 'key_excerpts' and any(x in pk.lower() for x in ['excerpt', 'quote', 'cite', 'extraction']):
                                            params[sk] = params.pop(pk)
                                            break

                        # Clean up parameters for common Pydantic validation issues
                        for k, v in list(params.items()):
                            # 1. Convert string boolean representations to actual booleans
                            if isinstance(v, str):
                                if v.lower() == "true":
                                    params[k] = True
                                elif v.lower() == "false":
                                    params[k] = False
                            
                            # 2. Extract string if a dict was returned for a string field
                            elif isinstance(v, dict):
                                field = schema.model_fields.get(k)
                                if field and 'str' in str(field.annotation):
                                    for sub_k in ['description', 'brief', 'text', 'value', 'query', 'topic']:
                                        if sub_k in v and isinstance(v[sub_k], str):
                                            params[k] = v[sub_k]
                                            break
                                    else:
                                        for sub_v in v.values():
                                            if isinstance(sub_v, str):
                                                params[k] = sub_v
                                                break
                        try:
                            return schema(**params)
                        except Exception:
                            pass
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
    raise last_err

def invoke_safe_tool_calling(model_with_tools, messages, is_async=False, max_retries=3, delay=2.0):
    """Safely invoke a tool-bound model, recovering from Groq's parser failures if possible."""
    
    async def _ainvoke():
        last_err = None
        for attempt in range(max_retries):
            try:
                return await model_with_tools.ainvoke(messages)
            except Exception as e:
                last_err = e
                try:
                    return _recover(e)
                except Exception:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
        raise last_err

    def _invoke():
        last_err = None
        for attempt in range(max_retries):
            try:
                return model_with_tools.invoke(messages)
            except Exception as e:
                last_err = e
                try:
                    return _recover(e)
                except Exception:
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
        raise last_err

    def _recover(e):
        body = getattr(e, "body", None)
        if body and isinstance(body, dict):
            error_info = body.get("error", {})
            failed_generation = error_info.get("failed_generation", "")
            if failed_generation:
                failed_generation = failed_generation.strip()
                tool_calls = []
                
                # Try parsing as JSON array/object directly (with block extraction if needed)
                try:
                    data = None
                    try:
                        data = json.loads(failed_generation)
                    except Exception:
                        # Extract code block or first bracketed section
                        match_code_block = re.search(r'```(?:json)?\s*(.*?)\s*```', failed_generation, re.DOTALL)
                        json_str = None
                        if match_code_block:
                            json_str = match_code_block.group(1).strip()
                        else:
                            start_idx = failed_generation.find('[') if failed_generation.find('[') < failed_generation.find('{') and failed_generation.find('[') != -1 else failed_generation.find('{')
                            end_idx = failed_generation.rfind(']') if failed_generation.rfind(']') > failed_generation.rfind('}') and failed_generation.rfind(']') != -1 else failed_generation.rfind('}')
                            if start_idx != -1 and end_idx != -1:
                                json_str = failed_generation[start_idx:end_idx+1].strip()
                        
                        if json_str:
                            json_str = json_str.replace("\\'", "'")
                            data = json.loads(json_str, strict=False)
                    
                    if data:
                        calls = data if isinstance(data, list) else [data]
                        for call in calls:
                            if isinstance(call, dict):
                                tool_name = call.get("name")
                                args = call.get("parameters") or call.get("args") or call
                                if tool_name and isinstance(args, dict):
                                    # Clean up arguments
                                    for k, v in list(args.items()):
                                        if isinstance(v, str):
                                            if v.lower() == "true":
                                                args[k] = True
                                            elif v.lower() == "false":
                                                args[k] = False
                                        elif isinstance(v, dict):
                                            for sub_k in ['description', 'brief', 'text', 'value', 'query', 'topic']:
                                                if sub_k in v and isinstance(v[sub_k], str):
                                                    args[k] = v[sub_k]
                                                    break
                                            else:
                                                for sub_v in v.values():
                                                    if isinstance(sub_v, str):
                                                        args[k] = sub_v
                                                        break
                                    tool_calls.append({
                                        "name": tool_name,
                                        "args": args,
                                        "id": "call_" + uuid.uuid4().hex[:12]
                                    })
                except Exception:
                    pass
                
                # Fallback to regex (XML format)
                if not tool_calls:
                    matches = re.finditer(r'<function=([^>]+)>(.*?)(?:</function>|$)', failed_generation, re.DOTALL)
                    for match in matches:
                        tool_name = match.group(1).strip()
                        json_str = match.group(2).strip()
                        json_str = json_str.replace("\\'", "'")
                        try:
                            data = json.loads(json_str, strict=False)
                            if isinstance(data, dict):
                                for k, v in list(data.items()):
                                    if isinstance(v, str):
                                        if v.lower() == "true":
                                            data[k] = True
                                        elif v.lower() == "false":
                                            data[k] = False
                                    elif isinstance(v, dict):
                                        for sub_k in ['description', 'brief', 'text', 'value', 'query', 'topic']:
                                            if sub_k in v and isinstance(v[sub_k], str):
                                                data[k] = v[sub_k]
                                                break
                                        else:
                                            for sub_v in v.values():
                                                if isinstance(sub_v, str):
                                                    data[k] = sub_v
                                                    break
                                tool_calls.append({
                                    "name": tool_name,
                                    "args": data,
                                    "id": "call_" + uuid.uuid4().hex[:12]
                                })
                        except Exception:
                            pass
                
                if tool_calls:
                    return AIMessage(content="", tool_calls=tool_calls)
        raise e

    return _ainvoke() if is_async else _invoke()

# ===== CONFIGURATION =====

summarization_model = init_chat_model(model="groq:meta-llama/llama-4-scout-17b-16e-instruct")
tavily_client = TavilyClient()

# ===== SEARCH FUNCTIONS =====

def tavily_search_multiple(
    search_queries: List[str], 
    max_results: int = 3, 
    topic: Literal["general", "news", "finance"] = "general", 
    include_raw_content: bool = True, 
) -> List[dict]:
    """Perform search using Tavily API for multiple queries.

    Args:
        search_queries: List of search queries to execute
        max_results: Maximum number of results per query
        topic: Topic filter for search results
        include_raw_content: Whether to include raw webpage content

    Returns:
        List of search result dictionaries
    """

    # Execute searches sequentially. Note: yon can use AsyncTavilyClient to parallelize this step.
    search_docs = []
    for query in search_queries:
        result = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic
        )
        search_docs.append(result)

    return search_docs

def summarize_webpage_content(webpage_content: str) -> str:
    """Summarize webpage content using the configured summarization model.

    Args:
        webpage_content: Raw webpage content to summarize

    Returns:
        Formatted summary with key excerpts
    """
    # =========================================================================
    # GROQ FREE-TIER RATE LIMIT FIX
    # The llama-3.1-8b-instant model on Groq's free tier has a strict Limit
    # of 6,000 Tokens Per Minute (TPM). 
    # Without this truncation, large webpages (e.g. 90,000+ tokens) would cause 
    # a 413 "Request too large" error and break the summarization step.
    # 
    # 15,000 characters is roughly 3,500 tokens. By truncating at this limit, 
    # we leave plenty of safe headroom so the sub-agents never crash!
    # =========================================================================
    max_chars = 6000
    if len(webpage_content) > max_chars:
        # Silently truncate without printing to avoid clobbering the interactive CLI prompt
        webpage_content = webpage_content[:max_chars] + "\n...[Content Truncated]..."
        
    try:
        # Generate summary using safe structured output helper
        summary = invoke_safe_structured_output(
            summarization_model,
            Summary,
            [
                HumanMessage(content=summarize_webpage_prompt.format(
                    webpage_content=webpage_content, 
                    date=get_today_str()
                ))
            ]
        )

        # Format summary with clear structure
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )

        return formatted_summary

    except Exception as e:
        failed_gen = ""
        body = getattr(e, "body", None)
        if body and isinstance(body, dict):
            failed_gen = body.get("error", {}).get("failed_generation", "")
        print(f"Failed to summarize webpage: {str(e)} | Failed gen: {failed_gen}")
        return webpage_content[:1000] + "..." if len(webpage_content) > 1000 else webpage_content

def deduplicate_search_results(search_results: List[dict]) -> dict:
    """Deduplicate search results by URL to avoid processing duplicate content.

    Args:
        search_results: List of search result dictionaries

    Returns:
        Dictionary mapping URLs to unique results
    """
    unique_results = {}

    for response in search_results:
        for result in response['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = result

    return unique_results

def process_search_results(unique_results: dict) -> dict:
    """Process search results by summarizing content where available.

    Args:
        unique_results: Dictionary of unique search results

    Returns:
        Dictionary of processed results with summaries
    """
    summarized_results = {}

    for url, result in unique_results.items():
        # Use existing content if no raw content for summarization
        if not result.get("raw_content"):
            content = result['content']
        else:
            # Summarize raw content for better processing
            content = summarize_webpage_content(result['raw_content'])

        summarized_results[url] = {
            'title': result['title'],
            'content': content
        }

    return summarized_results

def format_search_output(summarized_results: dict) -> str:
    """Format search results into a well-structured string output.

    Args:
        summarized_results: Dictionary of processed search results

    Returns:
        Formatted string of search results with clear source separation
    """
    if not summarized_results:
        return "No valid search results found. Please try different search queries or use a different search API."

    formatted_output = "Search results: \n\n"

    for i, (url, result) in enumerate(summarized_results.items(), 1):
        formatted_output += f"\n\n--- SOURCE {i}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "-" * 80 + "\n"

    return formatted_output

# ===== RESEARCH TOOLS =====

@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 3,
    topic: Annotated[Literal["general", "news", "finance"], InjectedToolArg] = "general",
) -> str:
    """Fetch results from Tavily search API with content summarization.

    Args:
        query: A single search query to execute
        max_results: Maximum number of results to return
        topic: Topic to filter results by ('general', 'news', 'finance')

    Returns:
        Formatted string of search results with summaries
    """
    # Execute search for single query
    search_results = tavily_search_multiple(
        [query],  # Convert single query to list for the internal function
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
    )

    # Deduplicate results by URL to avoid processing duplicate content
    unique_results = deduplicate_search_results(search_results)

    # Process results with summarization
    summarized_results = process_search_results(unique_results)

    # Format output for consumption
    return format_search_output(summarized_results)

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"
