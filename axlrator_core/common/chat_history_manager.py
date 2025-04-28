
from typing import Any, Dict
import uuid
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.ai import AIMessage
from axlrator_core.dataclasses.code_assist_data import ChatInfo, CodeChatInfo

def merge_ai_messages(messages: list[Dict[str, Any]]) -> list[ChatInfo]:
    merged_messages = {}
    
    for message in messages:
        if message.id not in merged_messages:
            merged_messages[message.id] = {
                'content': [],
                'additional_kwargs': message.additional_kwargs,
                'response_metadata': message.response_metadata,
                'id': message.id,
                'usage_metadata': getattr(message, 'usage_metadata', {}),
            }
        
        # Merge content
        if isinstance(message.content, list):
            merged_messages[message.id]['content'].extend(message.content)
        else:
            merged_messages[message.id]['content'].append({'text': message.content, 'type': 'text', 'index': 0})
    
    chat_infos = []
    for idx, (msg_id, msg_data) in enumerate(merged_messages.items()):
        content_text = ''.join([chunk['text'] for chunk in msg_data['content']])
        chat_infos.append(ChatInfo(
            seq=idx,
            messenger_type='02',
            message_body=content_text,
            send_time=''
        ))
    
    return chat_infos

def checkpoint_to_code_chat_info(thead_id, checkpoint) -> CodeChatInfo:
    if checkpoint is None:
        return None 
    messages = checkpoint.get('channel_values')['messages']
    
    human_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    
    chat_history = []
    
    # Add human messages
    for idx, message in enumerate(human_messages):
        chat_history.append(ChatInfo(
            seq=idx,
            messenger_type="01", # 01:user, 02:agent, 
            message_body=message.content,
            send_time='',
        ))
    
    # Add AI messages
    chat_history.extend(merge_ai_messages(ai_messages))
    
    # Assuming the first human message contains the question
    question = human_messages[0].content if human_messages else ""
    
    return CodeChatInfo(
        thread_id=thead_id,
        question=question,
        chat_history=chat_history
    )
