import json
import re
from typing import Dict, List, Optional


class DogFoodScorer:
    def __init__(self):
        self.starting_score = 100

    # -----------------------------
    # Carb % Calculation
    # -----------------------------
    def calculate_carb_percent(
        self,
        protein: float,
        fat: float,
        fiber: float,
        ash: float,
        moisture: float,
        food_type: str
    ) -> float:
        """
        Calculates carbohydrate percentage.
        - For dry foods: direct subtraction method
        - For wet/fresh foods: converts to dry matter basis
        """
        as_fed_carb = 100 - (protein + fat + fiber + ash + moisture)
        if as_fed_carb < 0:
            as_fed_carb = 0  # clamp to avoid negatives

        if food_type == "":
            if moisture > 17:
                dry_matter_carb = (as_fed_carb / (100 - moisture)) * 100
                return dry_matter_carb
            else:
                return as_fed_carb
        else:
            if food_type == "Dry Food":
                return as_fed_carb
            else:
                dry_matter_carb = (as_fed_carb / (100 - moisture)) * 100
                return dry_matter_carb

    # -----------------------------
    # 1. Food Type Deduction
    # -----------------------------

    def food_deduction(self, food_type: str) -> dict:
        max_deduction = -20
        deduction = -13
        if food_type == "Raw Food":
            deduction = 0
        elif food_type == "Fresh Food":
            deduction = -4
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": food_type, "score": score}

    # -----------------------------
    # 2. Sourcing Deduction
    # -----------------------------
    def sourcing_deduction(self, sourcing: str) -> dict:
        max_deduction = -15
        deduction = -10
        if sourcing == "":
            sourcing = "Human Grade (organic)"
        if sourcing == "Human Grade (organic)":
            deduction = 0
        elif sourcing == "Human Grade":
            deduction = -3
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": sourcing, "score": score}

    # -----------------------------
    # 3. Processing / Adulteration
    # -----------------------------
    def processing_deduction(self, food_type: str) -> dict:
        mapping = {
            "Uncooked (Not Frozen)": 0,
            "Uncooked (Flash Frozen)": -1,
            "Uncooked (Frozen)": -2,
            "Lightly Cooked": -3,
            "Lightly Cooked + Frozen": -4,
            "Freeze Dried": -5,
            "Air Dried": -7,
            "Dehydrated": -8,
            "Baked": -11,
            "Extruded": -15,
            "Retorted": -15,
            "": 0
        }
        return mapping.get(food_type, 0)

    def processing_base_topper(self, base_type: str, topper_type: Optional[str] = None) -> dict:
        max_deduction = -17
        base_deduction = self.processing_deduction(base_type)
        deduction = base_deduction
        print("base_deduction", base_deduction)
        if topper_type:
            topper_deduction = self.processing_deduction(topper_type)
            deduction = (base_deduction * 0.75) + (topper_deduction * 0.25)
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": base_type, "score": score}

    # -----------------------------
    # 4. Nutritionally Adequate
    # -----------------------------
    # def adequacy_deduction(self, base: bool, topper: Optional[bool] = None) -> int:
    #     if topper is None:
    #         return 0 if base else -35
    #     if base and not topper:
    #         return -10
    #     if not base and topper:
    #         return -26
    #     if not base and not topper:
    #         return -35
    #     return 0
    def adequacy_deduction(self, base: bool) -> dict:
        max_deduction = -14
        deduction = -10
        if base:
            deduction = 0
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": base, "score": score}

    # -----------------------------
    # 5. Starchy Carbohydrate %
    # -----------------------------
    def carb_deduction(self, carb_percent: float) -> dict:
        max_deduction = -14
        deduction = -10
        grade = "Above 30% starchy carbs"
        if carb_percent < 10:
            deduction = 0
            grade = "<10%"
        elif carb_percent <= 15:
            deduction = -2
            grade = "10-15% starchy carbs"
        elif carb_percent <= 20:
            deduction = -4
            grade = "16-20% starchy carbs"
        elif carb_percent <= 25:
            deduction = -6
            grade = "21-25% starchy carbs"
        elif carb_percent <= 30:
            deduction = -8
            grade = "26-30% starchy carbs"
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": grade, "score": score}

    # -----------------------------
    # 6. Ingredient Quality
    # -----------------------------
    # def ingredient_quality_deduction(self, qualities: List[str]) -> dict:
    #     max_deduction = -9
    #     values = {"high": 0, "good": 2, "moderate": 3, "low": 5}
    #     deduction = -5
    #     if not qualities:
    #         deduction = 0
    #     total = sum(values[q.lower()] for q in qualities if q.lower() in values)
    #     avg = total / len(qualities)
    #     if avg <= 1.0:
    #         deduction = -0
    #     elif avg <= 2.0:
    #         deduction = -2
    #     elif avg <= 3.5:
    #         deduction = -3
    #     score = (100 - (deduction/max_deduction)*100)
    #     return {"deduction": deduction, "grade": qualities, "score": score}

    # -----------------------------
    # 6. Protein Quality
    # -----------------------------
    def ingredient_quality_protein_deduction(self, protein_quality: str) -> dict:
        print("protein_quality", protein_quality)
        max_deduction = -9
        deduction = 0
        if not protein_quality:
            deduction = 0
        if protein_quality == "high":
            deduction = 0
        elif protein_quality == "good":
            deduction = -2
        elif protein_quality == "moderate":
            deduction = -3
        elif protein_quality == "low":
            deduction = -5
        score = (100 - (deduction/max_deduction)*100)
        print("score", score)
        return {"deduction": deduction, "grade": protein_quality, "score": score}

    # -----------------------------
    # 7. Fat Quality
    # -----------------------------
    def ingredient_quality_fat_deduction(self, fat_quality: str) -> dict:
        print("fat_quality", fat_quality)
        max_deduction = -9
        deduction = 0
        if not fat_quality:
            deduction = 0
        if fat_quality == "high":
            deduction = 0
        elif fat_quality == "good":
            deduction = -2
        elif fat_quality == "moderate":
            deduction = -3
        elif fat_quality == "low":
            deduction = -5
        score = (100 - (deduction/max_deduction)*100)
        print("score", score)
        return {"deduction": deduction, "grade": fat_quality, "score": score}

    # -----------------------------
    # 8. Fiber Quality
    # -----------------------------
    def ingredient_quality_fiber_deduction(self, fiber_quality: str) -> dict:
        print("fiber_quality", fiber_quality)
        max_deduction = -9
        deduction = 0
        if not fiber_quality:
            deduction = 0
        if fiber_quality == "high":
            deduction = 0
        elif fiber_quality == "good":
            deduction = -2
        elif fiber_quality == "moderate":
            deduction = -3
        elif fiber_quality == "low":
            deduction = -5
        score = (100 - (deduction/max_deduction)*100)
        print("score", score)
        return {"deduction": deduction, "grade": fiber_quality, "score": score}

    # -----------------------------
    # 9. Carbohydrate Quality
    # -----------------------------
    def ingredient_quality_carbohydrate_deduction(self, carbohydrate_quality: str) -> dict:
        print("carbohydrate_quality", carbohydrate_quality)
        max_deduction = -9
        deduction = 0
        if not carbohydrate_quality:
            deduction = 0
        if carbohydrate_quality == "high":
            deduction = 0
        elif carbohydrate_quality == "good":
            deduction = -2
        elif carbohydrate_quality == "moderate":
            deduction = -3
        elif carbohydrate_quality == "low":
            deduction = -5
        score = (100 - (deduction/max_deduction)*100)
        print("score", score)
        return {"deduction": deduction, "grade": carbohydrate_quality, "score": score}

    # -----------------------------
    # 10. Dirty Dozen Ingredients
    # -----------------------------
    def dirty_dozen_deduction(self, count: int) -> dict:
        max_deduction = -12
        deduction = -9
        grade = "10+ Added Dirty Dozen Ingredients"
        if count == 0 or count is None or count == "" or count == "0" or count == "null":
            deduction = 0
            grade = "0 Added Dirty Dozen Ingredients"
        elif count <= 2:
            deduction = -2
            grade = "1-2 Added Dirty Dozen Ingredients"
        elif count <= 5:
            deduction = -5
            grade = "3-5 Added Dirty Dozen Ingredients"
        elif count <= 9:
            deduction = -8
            grade = "6-9 Added Dirty Dozen Ingredients"
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": grade, "score": score}

    # -----------------------------
    # 11. Synthetic Nutrition Additions
    # -----------------------------
    def synthetic_deduction(self, count: int) -> dict:
        max_deduction = -9
        deduction = -5
        grade = ">11 Added Synthetic Ingredients"
        if count <= 3:
            deduction = 0
            grade = "0-3 Added Synthetic Ingredients (Vitamins E & D)"
        elif count <= 6:
            deduction = -2
            grade = "4-6 Added Synthetic Ingredients"
        elif count <= 10:
            deduction = -3
            grade = "7-10 Added Synthetic Ingredients"
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": grade, "score": score}

    # -----------------------------
    # 12. Longevity Additives
    # -----------------------------
    def longevity_deduction(self, months: int) -> dict:
        max_deduction = -4
        deduction = -4
        grade = ">7 Longevity Additives"
        if months == 0:
            deduction = 0
            grade = "0 Longevity Additives"
        elif months <= 3:
            deduction = -2
            grade = "1-3 Longevity Additives"
        elif months <= 7:
            deduction = -3
            grade = "4-7 Longevity Additives"
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": grade, "score": score}

    # -----------------------------
    # 13. Food Storage (Dry Only)
    # -----------------------------
    def storage_deduction_logic(self, storage: str) -> int:
        mapping = {
            "freezer": 0,
            "refrigerator": 0,
            "cool/dry space(yes)": -1,
            "cool/dry space(no)": -3,
            "": 0
        }
        return mapping.get(storage, 0)
    def storage_deduction(self, storage: str, topper_storage: str) -> dict:
        max_deduction = -4
        base_deduction = self.storage_deduction_logic(storage)
        deduction = base_deduction
        if topper_storage:
            topper_deduction = self.storage_deduction_logic(topper_storage)
            deduction = (base_deduction * 0.75) + (topper_deduction * 0.25)
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": storage, "score": score}

    # -----------------------------
    # 14. Packaging Size (Dry Only)
    # -----------------------------
    def packaging_deduction_logic(self, packaging_size: str) -> int:
        mapping = {
            "1 Month or less Supply": 0,
            "2 Month Supply": -3,
            "3+ Month Supply": -4,
            "": 0
        }
        return mapping.get(packaging_size, 0)
    def packaging_deduction(self, packaging_size: str, topper_packaging_size: str) -> dict:
        max_deduction = -7
        base_deduction = self.packaging_deduction_logic(packaging_size)
        deduction = base_deduction
        if topper_packaging_size:
            topper_deduction = self.packaging_deduction_logic(topper_packaging_size)
            deduction = (base_deduction * 0.75) + (topper_deduction * 0.25)
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": packaging_size, "score": score}


    # -----------------------------
    # 15. Shelf Life (Once Thawed)
    # -----------------------------
    def shelf_life_deduction_logic(self, shelf_life: str) -> int:
        mapping = {
            "<8 Days": 0,
            "2 Weeks": -3,
            "1 Month": -4,
            "": 0
        }
        return mapping.get(shelf_life, 0)
    def shelf_life_deduction(self, shelf_life: str, topper_shelf_life: str) -> dict:
        max_deduction = -7
        base_deduction = self.shelf_life_deduction_logic(shelf_life)
        deduction = base_deduction
        if topper_shelf_life:
            topper_deduction = self.shelf_life_deduction_logic(topper_shelf_life)
            deduction = (base_deduction * 0.75) + (topper_deduction * 0.25)
        score = (100 - (deduction/max_deduction)*100)
        return {"deduction": deduction, "grade": shelf_life, "score": score}

    # -----------------------------
    # Final Score Calculation
    # -----------------------------
    def calculate_score(self, deductions: List[int]) -> float:
        total_deduction = sum(deductions)
        score = self.starting_score + total_deduction
        return max(0, min(100, score))

    def classify_score(self, score: float) -> str:
        if score >= 85:
            return "Optimal"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Fair"
        elif score >= 30:
            return "Poor"
        return "At Risk"
