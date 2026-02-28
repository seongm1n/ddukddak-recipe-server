import json
import logging
from dataclasses import dataclass

from google import genai
from google.genai.types import GenerateContentConfig, Part

from app.core.config import get_settings
from app.core.exceptions import RecipeAnalysisException

logger = logging.getLogger(__name__)

settings = get_settings()

client = genai.Client(api_key=settings.gemini_api_key)

_RECIPE_PROMPT = """당신은 전문 레시피 분석가입니다. 이 요리 영상의 오디오를 분석하여 레시피를 추출하세요.

다음 JSON 형식으로만 응답하세요:

{
  "ingredients": [
    {"name": "김치", "quantity": "300", "unit": "g", "price": 3000, "note": "묵은지 권장"}
  ],
  "steps": ["김치를 한입 크기로 썬다", "돼지고기를 넣고 볶는다"],
  "servings": 2,
  "totalCost": 8500
}

규칙:
- 재료 가격은 한국 마트 기준 현실적인 가격 (원, KRW)
- 조리 순서는 명확하고 순서대로
- 인분 수가 언급되지 않으면 재료 양 기준으로 추정
- note는 특별한 팁이 있을 때만 포함
"""


@dataclass(frozen=True)
class IngredientData:
    name: str
    quantity: str
    unit: str
    price: int
    note: str | None = None


@dataclass(frozen=True)
class AnalyzedRecipe:
    ingredients: list[IngredientData]
    steps: list[str]
    total_cost: int
    servings: int


def analyze_recipe_from_audio(audio_path: str) -> AnalyzedRecipe:
    """Gemini API로 오디오 파일에서 레시피를 분석한다."""
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                Part.from_bytes(data=audio_bytes, mime_type="audio/mp4"),
                _RECIPE_PROMPT,
            ],
            config=GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )

        data = json.loads(response.text)

        required_keys = {"ingredients", "steps", "servings", "totalCost"}
        if not required_keys.issubset(data.keys()):
            logger.error("Missing keys in gemini response: %s", data.keys())
            raise RecipeAnalysisException()
        
        ingredients = [
            IngredientData(
                name=ing["name"],
                quantity=ing["quantity"],
                unit=ing["unit"],
                price=ing["price"],
                note=ing.get("note"),
            )
            for ing in data["ingredients"]
        ]

        return AnalyzedRecipe(
            ingredients=ingredients,
            steps=data["steps"],
            total_cost=data["totalCost"],
            servings=data["servings"],
        )
    
    except RecipeAnalysisException:
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini response: %s", e)
        raise RecipeAnalysisException()
    except Exception as e:
        logger.error("Recipe analysis failed: %s", e)
        raise RecipeAnalysisException()
