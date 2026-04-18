from flask import Blueprint, jsonify, request

from services.support_kb_service import SupportKBService

support_bp = Blueprint("support", __name__)
kb_service = SupportKBService()


@support_bp.route("/support/playbook", methods=["GET"])
def get_support_playbook():
    data = kb_service.get_catalog()
    categories = data.get("categories", [])

    summary = []
    for category in categories:
        summary.append(
            {
                "id": category.get("id"),
                "title": category.get("title"),
                "simpleCount": len(category.get("simple", [])),
                "complexCount": len(category.get("complex", [])),
            }
        )

    return jsonify({"success": True, "categories": summary}), 200


@support_bp.route("/support/faq", methods=["GET"])
def search_support_faq():
    query = request.args.get("query") or request.args.get("q")
    top_k = request.args.get("limit", 5, type=int)

    if not query:
        return jsonify(
            {"success": False, "message": "Query parameter is required (query or q)."}
        ), 400

    hits = kb_service.search_entries(query, top_k=max(1, min(top_k, 10)))
    return jsonify({"success": True, "query": query, "count": len(hits), "results": hits}), 200


@support_bp.route("/support/scenarios", methods=["GET"])
def get_support_scenarios():
    data = kb_service.get_catalog()
    categories = data.get("categories", [])

    scenarios = []
    for category in categories:
        category_id = category.get("id")
        category_title = category.get("title")

        for item in category.get("simple", []):
            scenarios.append(
                {
                    "categoryId": category_id,
                    "categoryTitle": category_title,
                    "difficulty": "simple",
                    "question": item.get("question"),
                    "expectedIntent": item.get("intention"),
                    "requiredData": item.get("required_data", []),
                    "expectedGuidance": item.get("recommended_answer"),
                }
            )

        for item in category.get("complex", []):
            scenarios.append(
                {
                    "categoryId": category_id,
                    "categoryTitle": category_title,
                    "difficulty": "complex",
                    "question": item.get("question"),
                    "expectedIntent": item.get("challenge"),
                    "requiredData": item.get("required_data", []),
                    "expectedGuidance": item.get("recommended_answer")
                    or item.get("expected"),
                }
            )

    return jsonify({"success": True, "count": len(scenarios), "scenarios": scenarios}), 200

