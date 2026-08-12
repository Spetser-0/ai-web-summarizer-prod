import os
import json
import time
from typing import Dict, Any, List
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from dotenv import load_dotenv

load_dotenv(override=True)

class SummarizationError(Exception):
    """Custom exception raised when summarization fails."""
    pass


def get_summarization_prompt(text: str, mode: str) -> str:
    """
    Constructs the system prompt and instructions based on the mode.
    
    Args:
        text (str): The cleaned webpage text to summarize.
        mode (str): The mode ('quick', 'detailed', or 'competitor').
        
    Returns:
        str: The full instructions prompt.
    """
    base_instructions = (
        "You are a professional research and summarization assistant.\n"
        "Analyze the text provided below and return your response STRICTLY as a JSON object with the following keys:\n"
        "1. \"summary\": A string containing the text summary.\n"
        "2. \"key_points\": A list of strings representing the key takeaways or insights.\n\n"
        "CRITICAL: Return ONLY valid, parseable JSON. Do not include markdown code block syntax (like ```json ... ```), no introductory text, and no postscript explanation. Your entire response must be a single JSON object."
    )
    
    if mode == "quick":
        mode_instructions = (
            "For 'quick' mode:\n"
            "- \"summary\": Provide a concise 1-2 paragraph overview of the main topic and core message.\n"
            "- \"key_points\": Extract exactly 3 high-impact bullet points containing the most essential takeaways."
        )
    elif mode == "detailed":
        mode_instructions = (
            "For 'detailed' mode:\n"
            "- \"summary\": Provide a comprehensive analysis (3-4 paragraphs) covering the background, main arguments, key themes, and broader context.\n"
            "- \"key_points\": Extract 5 to 8 detailed, actionable insights, supporting evidence, or sub-themes found in the text."
        )
    elif mode == "competitor":
        mode_instructions = (
            "For 'competitor' mode (business-focused competitive analysis):\n"
            "- \"summary\": Provide a strategic overview of the company, service, or topic, analyzing its value proposition, target market, and business/monetization model.\n"
            "- \"key_points\": Extract 4 to 6 strategic points identifying direct competitors, competitive advantages, potential weaknesses/risks, and market opportunities."
        )
    else:
        # Fallback
        mode_instructions = (
            "Provide a general summary of the text and 3 key points."
        )

    return (
        f"{base_instructions}\n\n"
        f"--- Mode instructions ---\n"
        f"{mode_instructions}\n\n"
        f"--- Text to analyze ---\n"
        f"{text}"
    )


def _generate_mock_summary(text: str, mode: str) -> Dict[str, Any]:
    """Generates a static mock summary based on the text contents and mode."""
    is_hn = "hacker news" in text.lower() or "ycombinator" in text.lower()
    if is_hn:
        if mode == "quick":
            return {
                "summary": "Hacker News is a community-driven news aggregator focused on computer science and entrepreneurship. Users submit posts, which are dynamically ranked based on community upvotes and time-based score decay.",
                "key_points": [
                    "Operates as a minimal, text-based platform for tech discussions and start-up news.",
                    "Curated dynamically by community voting, maintaining strict moderation and discussion quality.",
                    "Serves as a primary reference point for developers, engineers, and tech founders."
                ]
            }
        elif mode == "detailed":
            return {
                "summary": "Hacker News is a social news website operated by the startup incubator Y Combinator. The platform acts as a major hub for sharing technical articles, startup news, and general interest items for computer scientists and programmers. Its minimal design emphasizes fast load times and clean, readable text threads, avoiding the heavy visual styling of contemporary social networks.",
                "key_points": [
                    "Owned and maintained by Y Combinator, serving as a talent and idea incubator.",
                    "Implements a scoring algorithm where value decays rapidly over time to ensure homepage freshness.",
                    "Supports a highly active comment section governed by strict guidelines of civility and intellectual curiosity.",
                    "Features 'Show HN' for creators presenting their projects and 'Ask HN' for community questions.",
                    "Provides job boards displaying openings from Y Combinator-backed startups."
                ]
            }
        else: # competitor
            return {
                "summary": "Hacker News is a highly specialized community platform competing in the social sharing and developer community space. While not a commercial venture in the traditional sense, it acts as a primary marketing and talent acquisition funnel for its parent organization, Y Combinator.",
                "key_points": [
                    "Positioned as a high-authority forum for early adopters and tech decision makers.",
                    "Competes indirectly with platforms like Reddit (specifically tech subreddits), Dev.to, and Twitter.",
                    "Value proposition lies in its highly concentrated pool of experienced engineers and founders.",
                    "Key risk includes potential stagnation of the community guidelines or echo-chamber dynamics."
                ]
            }
    else:
        # Generic mock
        if mode == "quick":
            return {
                "summary": "This is a quick summary of the analyzed webpage. The content covers key developments and highlights within the scope of the target article's topic.",
                "key_points": [
                    "Primary takeaway of the article's core arguments and facts.",
                    "Secondary supporting detail showing the context of the discussion.",
                    "A concluding conclusion outlining future implications."
                ]
            }
        elif mode == "detailed":
            return {
                "summary": "This is a detailed analysis of the scraped webpage content. The article investigates the structural changes, major themes, and underlying assumptions in the text. It highlights key evidence provided by the author to support their claims and contextualizes these findings within the industry.",
                "key_points": [
                    "Detailed insight regarding the main themes analyzed.",
                    "Core data point or piece of evidence extracted from the text.",
                    "Strategic implication of the changes discussed.",
                    "Potential drawbacks or counterarguments outlined in the source content.",
                    "Future outlook and recommendations based on the analysis."
                ]
            }
        else: # competitor
            return {
                "summary": "This is a competitive analysis summarizing the business model, target audience, and market position of the organization or topic described in the text.",
                "key_points": [
                    "Core value proposition and primary customer segment.",
                    "Identified monetization model and pricing strategies.",
                    "Key strengths and competitive advantages over current alternatives.",
                    "Potential vulnerabilities, market threats, and business weaknesses."
                ]
            }


def summarize_text(text: str, mode: str) -> Dict[str, Any]:
    """
    Summarizes the given text using the Google Gemini API.
    
    Args:
        text (str): The text content to summarize.
        mode (str): Summarization mode ('quick', 'detailed', or 'competitor').
        
    Returns:
        Dict[str, Any]: A dictionary containing 'summary' (str) and 'key_points' (List[str]).
        
    Raises:
        SummarizationError: If the Gemini API fails (after 1 retry) or returns invalid JSON.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    allow_mock = os.environ.get("ALLOW_MOCK_SUMMARY", "true").lower() in ("true", "1", "yes")

    if not api_key or api_key.strip() == "" or api_key == "your_gemini_api_key_here" or api_key == "mock":
        if allow_mock:
            print("[Summarizer] WARNING: Gemini API key is not configured. Running in MOCK mode.")
            return _generate_mock_summary(text, mode)
        else:
            raise SummarizationError("Gemini API key is not configured. Please set GEMINI_API_KEY in the .env file.")

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
    client = genai.Client(api_key=api_key)
    
    prompt = get_summarization_prompt(text, mode)

    # Retry mechanism: Try twice (initial attempt + 1 retry)
    max_attempts = 2
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            # We truncate the input text if it's excessively long to avoid hitting token limits
            # 100,000 characters is roughly 20,000 - 25,000 tokens, which fits comfortably in Claude's context window.
            truncated_text_prompt = prompt
            if len(prompt) > 120000:
                truncated_text_prompt = get_summarization_prompt(text[:100000] + "\n[Content Truncated for Length]...", mode)
                
            response = client.models.generate_content(
                model=model,
                contents=truncated_text_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4000,
                )
            )
            
            response_content = response.text.strip()
            
            # Clean possible markdown wrapping if the LLM ignored instructions
            if response_content.startswith("```"):
                # strip out ```json and ```
                lines = response_content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_content = "\n".join(lines).strip()
            
            parsed_json = json.loads(response_content)
            
            # Basic structural validation
            if not isinstance(parsed_json, dict) or "summary" not in parsed_json or "key_points" not in parsed_json:
                raise ValueError("JSON response structure is invalid.")
                
            if not isinstance(parsed_json["key_points"], list):
                parsed_json["key_points"] = [str(parsed_json["key_points"])]
                
            return {
                "summary": str(parsed_json["summary"]),
                "key_points": [str(pt) for pt in parsed_json["key_points"]]
            }

        except genai_errors.APIError as e:
            last_error = e
            print(f"[Summarizer] Attempt {attempt} failed with API error: {str(e)}")
            if attempt < max_attempts:
                time.sleep(2)  # Wait before retry
                continue
        except json.JSONDecodeError as e:
            last_error = ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
            print(f"[Summarizer] Attempt {attempt} returned invalid JSON structure.")
            if attempt < max_attempts:
                time.sleep(1)
                continue
        except Exception as e:
            last_error = e
            print(f"[Summarizer] Attempt {attempt} failed with unexpected error: {str(e)}")
            if attempt < max_attempts:
                time.sleep(1)
                continue

    if allow_mock:
        print(f"[Summarizer] WARNING: API calls failed. ALLOW_MOCK_SUMMARY is true. Falling back to MOCK mode. Error detail: {str(last_error)}")
        return _generate_mock_summary(text, mode)

    raise SummarizationError(f"Summarization failed after {max_attempts} attempts. Details: {str(last_error)}")
