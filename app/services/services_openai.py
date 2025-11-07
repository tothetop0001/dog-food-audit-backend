import requests
import json

class OpenAIService:
  def __init__(self):
    self.header = {
      "Authorization": "Bearer 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",
      "Content-Type": "application/json"
    }
    self.data = {
        "model": "gpt-4o-mini",
        "instructions": "You are a helpful assistant that can answer questions and help with tasks.",
        "input": "I want to get the following information of Purina Pro Plan Sensitive Skin and Stomach Puppy Large Breed Salmon & Rice Formula with only JSON structure. 1. brand: 2. processing_method: 3. adulteration_method: 4. nutritional_adequacy: 5. shelf_life: 6. storage_type: 7. description: 8. guaranteed_analysis: 9. ingredients: 10. serving_size: 11. feeding_guideline: // Here, I want to get with string for explain 12. container_weight: 13. num_serving: 14. website_url: 15. brand: 2. processing_method: 3. adulteration_method: 4. nutritional_adequacy: 5. shelf_life: 6. storage_type: 7. description: 8. guaranteed_analysis: 9. ingredients: 10. serving_size: 11. feeding_guideline: // Here, I want to get with string for explain 12. container_weight: 13. num_serving: 14. website_url:"
    }

  async def get_result(self):
    response = requests.post(
      "https://api.openai.com/v1/responses",
      headers=self.header,
      json=self.data
    )

    response = json.loads(response.text)
    response = response['output'][0]['content'][0]['text']

    print("response!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", response)

  async def analyze_results(self, results):
    response = requests.post(
      "https://api.openai.com/v1/responses",
      headers=self.header,
      json=self.data
    )
    response = json.loads(response.text)
    print("response", response['output'][0]['text'])