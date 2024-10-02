from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


CODE_SUMMARY_GENERATE_PROMPT = PromptTemplate.from_template("""
Your job is to process a given code chunk, which represents a single function, and add contextual information to it. 

You will be provided with the following inputs:
<code_chunk>
{CODE_CHUNK}
</code_chunk>

Follow these steps to process the code chunk and add contextual information:

1. Analyze the code chunk:
   - Determine the purpose of the function
   - Note any important algorithms or data structures used
   - Identify input parameters and return values

2. Add contextual information:
   - Summarize the function's purpose in one sentence
   - List key features or operations performed by the function
   - Mention any notable dependencies or libraries used

3. Create the output in the following format:
   <augmented_chunk>
   <metadata>
   <function_name>[Insert function name here]</function_name>
   <summary>[Insert one-sentence summary here]</summary>
   <features>
   - [Feature 1]
   - [Feature 2]
   - [Feature 3]
   </features>
   </metadata>
   <code>
   [Insert the original code chunk here]
   </code>
   </augmented_chunk>

Here's an example of how your output should look:

<augmented_chunk>
<metadata>
<function_name>reverse_string</function_name>
<summary>Reverses the input string using a two-pointer approach.</summary>
<features>
- Uses two pointers to swap characters
- Handles Unicode strings correctly
- In-place reversal for memory efficiency
</features>
</metadata>
<code>
def reverse_string(s: str) -> str:
    chars = list(s)
    left, right = 0, len(chars) - 1
    while left < right:
        chars[left], chars[right] = chars[right], chars[left]
        left += 1
        right -= 1
    return ''.join(chars)
</code>
</augmented_chunk>

Process the given code chunk and produce the augmented chunk with added contextual information. Ensure that your analysis is accurate and the added information is relevant and helpful for understanding the code's purpose and functionality.
""")

CODE_ASSIST_PROMPT = PromptTemplate.from_template("""
You are an AI assistant designed to predict the next lines of code a programmer might write. Your task is to analyze the existing code and context provided, then generate a prediction for what the programmer might write next.

Here is the existing code:
<existing_code>
{EXISTING_CODE}
</existing_code>

The programming language being used is:
<language>
{PROGRAMMING_LANGUAGE}
</language>

Additional context (if any):
<context>
{CONTEXT}
</context>

Please follow these steps:

1. Analyze the existing code, paying attention to:
   - The overall structure and purpose of the code
   - Any patterns or conventions being used
   - Incomplete functions or blocks that might need to be finished
   - Potential next logical steps in the development process

2. Consider the programming language and any language-specific conventions or best practices.

3. Take into account any additional context provided about the project or the programmer's intentions.

4. Based on your analysis, generate a prediction for the next lines of code the programmer might write. Your prediction should:
   - Be a natural continuation of the existing code
   - Follow the established style and conventions
   - Be syntactically correct for the specified programming language
   - Address any obvious next steps or complete any unfinished structures in the code

5. Output your prediction in the following format:

<prediction>
// Your predicted code here
</prediction>

6. After your prediction, provide a brief explanation of your reasoning:

<explanation>
Explain why you predicted this code, referencing specific elements of the existing code, the programming language, or the provided context that influenced your decision.
</explanation>

Remember, your goal is to provide a helpful and accurate prediction that a programmer would find useful and relevant. Be creative yet practical in your suggestions, always keeping in mind the context and purpose of the existing code.


""")
