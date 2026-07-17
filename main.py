from server import OceanicOSService


def main() -> None:
    service = OceanicOSService()
    print("Health:", service.health())
    print("Plan:", service.create_plan("Draft an orchestration update"))
    service.store_memory({"text": "Preserve decision context", "source": "demo"})
    print("Memory:", service.search_memory("decision"))
    print("Tool:", service.invoke_tool("echo", {"message": "OceanicOS ready"}))


if __name__ == "__main__":
    main()
