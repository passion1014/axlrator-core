from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


TERM_CONVERSION_PROMPT1 = PromptTemplate.from_template("""
You are an AI assistant specialized in conversion <korean_term> into programming variable. Your task is to provide appropriate conversion that can be used as variable names, table names, column names, or class names in code.

Here is the Korean term you need to convert:
<korean_term>
{korean_term}
</korean_term>

Only use the words in <related_info> for the conversion, and if there are no applicable words, do not convert. exact match only.

<related_info>
{related_info}
</related_info>

Provide only the answer in the following format without any explanation::
<answer>
snake_case: [snake_case_변환]
camel_case: [camelCase변환]
</answer>

""")
# 24.11.12 이전버전
# TERM_CONVERSION_PROMPT = PromptTemplate.from_template("""
# You are an AI assistant specialized in conversion Korean terms into English for programming contexts. Your task is to provide appropriate English conversion that can be used as variable names, table names, column names, or class names in code.

# Here is the Korean term you need to convert:
# <korean_term>
# {korean_term}
# </korean_term>

# Use only the information in related_info to inform your conversion decision, ignoring any outside context or definitions not found within related_info.

# Here is some related information to help with the conversion:
# <related_info>
# {related_info}
# </related_info>

# Please follow these steps:
# 1. Convert the given Korean term into an English programming term.
# 2. Consider any programming-related rules or restrictions that might influence the conversion.
# 3. Choose the most appropriate conversion for programming use.
# 4. Convert the result into snake_case and camelCase formats.
# 5. Explain the reason for the chosen conversion.

# Provide only the answer in the following format without any explanation::
# <answer>
# snake_case: [snake_case_변환]
# camel_case: [camelCase변환]
# </answer>
# """)


TERM_CONVERSION_PROMPT2 = PromptTemplate.from_template("""
You are an AI that assists with programming.  

1. Identify Korean words in the provided Java source code and convert them into English words using camelCase.  
2. When converting, use the "Glossary" below to ensure consistent translation.  
3. Represent all translated words in camelCase format.  
4. If a word does not exist in the glossary, leave it untranslated.  
5. Add a comment at the end of the line with the format // [original Korean] for each line containing a translated word.  

[Example]  
Input: String 선수수수료;
Output: String prrcPrmm = null;  // 선수수수료

<input>
{request}
</input>

<vocabulary>  
{context}
</vocabulary>  

only print output without explanation!
""")
# 너는 프로그램 작성을 도와주는 AI야.
# 1. 입력된 JAVA 소스코드에서 한국어 단어가 있으면 그것을 영단어(camel case)로 변환한다.
# 2. 영단어로 변환할때 하단의 "용어집"을 반드시 사용해서 변환한다.
# 3. 변환된 영단어는 camelCase로 표현한다.
# 4. 만약 용어집에 없는 단어가 등장하면 변환하지 않고 그대로 둔다.
# 5. 변환된 단어가 존재하는 라인의 끝에는 [변환 전 한글]로 // 주석을 추가한다.

# [example]
# 입력 : String 선수수수료;
# 결과 : String prrcPrmm = null;	//선수수수료

# <변환 대상 소스코드>
# {{request}}
# </변환 대상 소스코드>

# <용어집>
# {{context}}
# </용어집>
