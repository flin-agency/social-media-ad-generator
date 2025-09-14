"""Question templates for different product categories."""

from typing import Dict, List
from ..models import ProductCategory, QuestionTemplate

QUESTION_TEMPLATES: Dict[str, List[QuestionTemplate]] = {
    "base_questions": [
        QuestionTemplate(
            question_id="target_audience",
            template="Who is your target customer? (e.g., young professionals, parents, fitness enthusiasts, etc.)",
            follow_up_questions=[
                "What age range?",
                "What are their main interests?",
                "What problems do they face that your product solves?"
            ]
        ),
        QuestionTemplate(
            question_id="brand_tone",
            template="What tone should your ad convey? (professional, playful, luxury, minimalist, bold, friendly, sophisticated)",
            follow_up_questions=[
                "Should it feel premium or accessible?",
                "Formal or casual communication style?"
            ]
        ),
        QuestionTemplate(
            question_id="key_message",
            template="What's the main selling point or call-to-action for your product?",
            follow_up_questions=[
                "What makes your product unique?",
                "What action do you want viewers to take?",
                "What's the primary benefit customers get?"
            ]
        )
    ],

    ProductCategory.FASHION.value: [
        QuestionTemplate(
            question_id="fashion_style",
            template="What style aesthetic best describes your target customers? (minimalist, bohemian, streetwear, classic, trendy, etc.)",
            category_specific=[ProductCategory.FASHION]
        ),
        QuestionTemplate(
            question_id="fashion_occasion",
            template="What occasion or season is this product designed for? (everyday wear, special events, work, casual, seasonal, etc.)",
            category_specific=[ProductCategory.FASHION]
        ),
        QuestionTemplate(
            question_id="fashion_demographics",
            template="What's the primary age group and gender for this fashion item?",
            category_specific=[ProductCategory.FASHION]
        )
    ],

    ProductCategory.ELECTRONICS.value: [
        QuestionTemplate(
            question_id="tech_benefits",
            template="What are the key technical features or benefits we should highlight? (performance, convenience, innovation, etc.)",
            category_specific=[ProductCategory.ELECTRONICS]
        ),
        QuestionTemplate(
            question_id="tech_audience",
            template="Are you targeting tech enthusiasts, general consumers, or professionals?",
            category_specific=[ProductCategory.ELECTRONICS]
        ),
        QuestionTemplate(
            question_id="tech_problem",
            template="What specific problem or need does this electronic product solve?",
            category_specific=[ProductCategory.ELECTRONICS]
        )
    ],

    ProductCategory.FOOD_BEVERAGE.value: [
        QuestionTemplate(
            question_id="food_occasion",
            template="What eating or drinking occasion is this for? (breakfast, snack, dinner, celebration, workout, etc.)",
            category_specific=[ProductCategory.FOOD_BEVERAGE]
        ),
        QuestionTemplate(
            question_id="food_appeal",
            template="Should we emphasize taste, health benefits, convenience, or tradition?",
            category_specific=[ProductCategory.FOOD_BEVERAGE]
        ),
        QuestionTemplate(
            question_id="food_dietary",
            template="Are there specific dietary preferences we should highlight? (vegan, gluten-free, organic, low-calorie, etc.)",
            category_specific=[ProductCategory.FOOD_BEVERAGE]
        )
    ],

    ProductCategory.BEAUTY_PERSONAL_CARE.value: [
        QuestionTemplate(
            question_id="beauty_concerns",
            template="What beauty concerns or goals does this product address? (anti-aging, hydration, acne, glow, etc.)",
            category_specific=[ProductCategory.BEAUTY_PERSONAL_CARE]
        ),
        QuestionTemplate(
            question_id="beauty_routine",
            template="When in their beauty routine would someone use this? (morning, evening, weekly treatment, daily care, etc.)",
            category_specific=[ProductCategory.BEAUTY_PERSONAL_CARE]
        ),
        QuestionTemplate(
            question_id="beauty_skin_type",
            template="What skin types or beauty preferences should we focus on? (sensitive, oily, dry, all skin types, etc.)",
            category_specific=[ProductCategory.BEAUTY_PERSONAL_CARE]
        )
    ],

    ProductCategory.HOME_GARDEN.value: [
        QuestionTemplate(
            question_id="home_space",
            template="What area of the home or garden is this for? (living room, kitchen, bedroom, outdoor, etc.)",
            category_specific=[ProductCategory.HOME_GARDEN]
        ),
        QuestionTemplate(
            question_id="home_lifestyle",
            template="What lifestyle or home aesthetic are you targeting? (modern, cozy, minimalist, rustic, etc.)",
            category_specific=[ProductCategory.HOME_GARDEN]
        ),
        QuestionTemplate(
            question_id="home_benefit",
            template="What's the main benefit - decoration, functionality, comfort, or organization?",
            category_specific=[ProductCategory.HOME_GARDEN]
        )
    ],

    ProductCategory.SPORTS_OUTDOORS.value: [
        QuestionTemplate(
            question_id="sports_activity",
            template="What sport or outdoor activity is this designed for? (running, yoga, hiking, gym, cycling, etc.)",
            category_specific=[ProductCategory.SPORTS_OUTDOORS]
        ),
        QuestionTemplate(
            question_id="sports_level",
            template="What fitness level are you targeting? (beginners, recreational users, serious athletes, professionals)",
            category_specific=[ProductCategory.SPORTS_OUTDOORS]
        ),
        QuestionTemplate(
            question_id="sports_motivation",
            template="What motivates your target customers? (fitness goals, outdoor adventure, competition, wellness, etc.)",
            category_specific=[ProductCategory.SPORTS_OUTDOORS]
        )
    ],

    ProductCategory.SERVICES.value: [
        QuestionTemplate(
            question_id="service_problem",
            template="What specific problem or need does your service solve for customers?",
            category_specific=[ProductCategory.SERVICES]
        ),
        QuestionTemplate(
            question_id="service_clients",
            template="Who are your ideal clients? (individuals, small businesses, enterprises, specific industries)",
            category_specific=[ProductCategory.SERVICES]
        ),
        QuestionTemplate(
            question_id="service_value",
            template="What's the key value proposition - save time, save money, expertise, convenience, or results?",
            category_specific=[ProductCategory.SERVICES]
        )
    ]
}


def get_questions_for_category(category: ProductCategory, num_questions: int = 3) -> List[QuestionTemplate]:
    """Get appropriate questions for a product category."""
    questions = []

    # Always include base questions first
    base_questions = QUESTION_TEMPLATES["base_questions"]
    questions.extend(base_questions[:min(num_questions, len(base_questions))])

    # Add category-specific questions if available
    if len(questions) < num_questions and category.value in QUESTION_TEMPLATES:
        category_questions = QUESTION_TEMPLATES[category.value]
        remaining_slots = num_questions - len(questions)
        questions.extend(category_questions[:remaining_slots])

    return questions[:num_questions]