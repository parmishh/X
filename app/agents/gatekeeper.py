import json
import base64
import mimetypes
import asyncio
import requests
from pydantic import BaseModel
from app.core.state import ClaimState
from app.agents.base import BaseAgent

# Updated schema to expect forgery detection
class DocTypeCheck(BaseModel):
    actual_document_type: str
    is_readable: bool
    quality_issue: str = ""
    is_ai_forged: bool = False
    forgery_reason: str = ""

class GatekeeperAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    async def validate_documents(self, state: ClaimState, raw_files: dict) -> bool:
        all_passed = True

        for index, doc in enumerate(state.documents):
            file_bytes = raw_files[doc.file_id]
            mime_type, _ = mimetypes.guess_type(doc.file_name)
            if not mime_type:
                mime_type = "image/jpeg"
            
            base64_image = base64.b64encode(file_bytes).decode('utf-8')
            image_url = f"data:{mime_type};base64,{base64_image}"
            
            # Dynamically inject the AI checker instructions if enabled
            forgery_instructions = ""
            if state.enable_ai_forgery_check:
                forgery_instructions = """
                CRITICAL SECURITY CHECK: You must also analyze this image for AI generation or digital forgery. 
                Look for: unnatural text rendering, impossible geometric angles, lack of physical paper imperfections, or hallmarks of AI generation (Midjourney/DALL-E artifacts).
                Set "is_ai_forged" to true if you strongly suspect this is an AI-generated fake, and explain why in "forgery_reason".
                """
            else:
                forgery_instructions = """
                "is_ai_forged" should always be false, and "forgery_reason" should be empty.
                """

            prompt = f"""
            You are a medical document classifier. 
            Identify the document type. Is it a {doc.required_type}?
            If it is completely blurry and unreadable, set is_readable to false and explain why in quality_issue.
            
            {forgery_instructions}
            
            Return ONLY valid JSON. Do not include markdown formatting.
            Use this exact JSON structure:
            {{
                "actual_document_type": "string",
                "is_readable": boolean,
                "quality_issue": "string",
                "is_ai_forged": boolean,
                "forgery_reason": "string"
            }}
            """
            
            try:
                def make_request():
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": self.model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": image_url}}
                                ]
                            }
                        ],
                        "temperature": 0.0
                    }
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                    resp.raise_for_status()
                    return resp.json()

                response_data = await self.execute_with_retry(
                    lambda: asyncio.to_thread(make_request), 
                    max_retries=3
                )
                
                if "choices" not in response_data or not response_data["choices"]:
                    raise Exception(f"OpenRouter returned invalid format: {response_data}")

                raw_text = response_data["choices"][0]["message"]["content"].strip()
                
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:-3].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:-3].strip()

                raw_json = json.loads(raw_text)
                check_result = DocTypeCheck(**raw_json)
                
                # Check 1: AI Forgery
                if check_result.is_ai_forged:
                    state.log("Gatekeeper", f"Forgery Check {doc.file_name}", "FAILED", f"AI Generation Suspected: {check_result.forgery_reason}")
                    state.rejection_reasons.append(f"Security Alert: The document '{doc.file_name}' has been flagged as potentially AI-generated or digitally manipulated. Claim halted.")
                    all_passed = False
                    continue
                elif state.enable_ai_forgery_check:
                    state.log("Gatekeeper", f"Forgery Check {doc.file_name}", "SUCCESS", "Document passed authenticity check.")

                # Check 2: Readability
                if not check_result.is_readable:
                    state.log("Gatekeeper", f"Check {doc.file_name}", "FAILED", "Document is blurry or illegible.")
                    state.rejection_reasons.append(f"The file '{doc.file_name}' is unreadable. {check_result.quality_issue} Please re-upload a clear copy.")
                    all_passed = False
                    continue
                    
                # Check 3: Document Type
                if check_result.actual_document_type.upper() != doc.required_type.upper():
                    if doc.required_type.upper().replace("_", " ") not in check_result.actual_document_type.upper():
                        state.log("Gatekeeper", f"Check {doc.file_name}", "FAILED", f"Type mismatch. Expected {doc.required_type}, found {check_result.actual_document_type}.")
                        state.rejection_reasons.append(f"You uploaded a {check_result.actual_document_type} for '{doc.file_name}', but this claim requires a {doc.required_type}. Please upload the correct document.")
                        all_passed = False
                        continue
                
                doc.actual_type = check_result.actual_document_type.upper()
                doc.is_valid = True
                state.log("Gatekeeper", f"Check {doc.file_name}", "SUCCESS", f"Validated as {doc.actual_type}.")

            except Exception as e:
                print(f"\n[CRITICAL] Nemotron Gatekeeper Error on {doc.file_name}: {str(e)}\n")
                raise Exception(f"Gatekeeper Agent Failed: {str(e)}")

            if index < len(state.documents) - 1:
                await asyncio.sleep(2)

        return all_passed