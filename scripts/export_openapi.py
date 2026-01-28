import json
from fastapi.openapi.utils import get_openapi
from decisionos.api.main import app

def export_openapi():
    """
    Export the OpenAPI schema to a JSON file.
    Useful for generating clients or external documentation.
    """
    with open("openapi.json", "w") as f:
        json.dump(
            get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
            ),
            f,
            indent=2
        )
    print("Exported openapi.json")

if __name__ == "__main__":
    export_openapi()
